import json
import os
import time
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv


MODEL_DIR_CANDIDATES = [
    Path(__file__).resolve().parent / "saved_models",
    Path(__file__).resolve().parent.parent.parent / "saved_models",
]

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def _resolve_model_path(filename: str) -> Path:
    for directory in MODEL_DIR_CANDIDATES:
        candidate = directory / filename
        if candidate.exists():
            return candidate

    return MODEL_DIR_CANDIDATES[0] / filename


MODEL_PATH = _resolve_model_path("best_delay_regressor.joblib")
MODEL_METADATA_PATH = _resolve_model_path("best_delay_regressor_metadata.json")

FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

WEATHER_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "wind_speed_10m",
]


class UpstreamServiceError(Exception):
    """Raised when an external dependency fails or is temporarily unavailable."""


def _round_to_nearest_hour(value: datetime) -> datetime:
    rounded = value.replace(second=0, microsecond=0, minute=0)
    if value.minute >= 30:
        rounded += timedelta(hours=1)
    return rounded


def _ensure_naive_local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.replace(tzinfo=None)


@lru_cache(maxsize=1)
def load_prediction_bundle():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {MODEL_PATH}. "
            "Train the regression model before calling the prediction API."
        )

    model = joblib.load(MODEL_PATH)

    metadata = {
        "model_name": "unknown",
        "decision_threshold_minutes": 0.0,
        "prediction_rule": (
            "Return NO DELAY when predicted delay is strictly below 0 minutes."
        ),
    }

    if MODEL_METADATA_PATH.exists():
        metadata.update(json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8")))

    return model, metadata


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_city_from_db(iata_code: str) -> dict:
    query = """
        SELECT
            id_city,
            name_city,
            latitude_city,
            longitude_city
        FROM city
        WHERE id_city = %s
    """

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (iata_code,))
            result = cursor.fetchone()

    if not result:
        raise ValueError(f"Unknown IATA code '{iata_code}'.")

    return {
        "id_city": result[0],
        "name_city": result[1],
        "latitude": float(result[2]),
        "longitude": float(result[3]),
    }


def get_estimated_duration(origin: str, destination: str) -> tuple[int, str, int]:
    query = """
        WITH route_stats AS (
            SELECT
                ROUND(AVG(estimated_duration))::int AS route_avg_duration,
                COUNT(*)::int AS route_observations
            FROM gold_flights
            WHERE origin_id_city = %s
              AND dest_id_city = %s
        ),
        global_stats AS (
            SELECT ROUND(AVG(estimated_duration))::int AS global_avg_duration
            FROM gold_flights
        )
        SELECT
            COALESCE(route_stats.route_avg_duration, global_stats.global_avg_duration) AS estimated_duration,
            route_stats.route_observations
        FROM route_stats
        CROSS JOIN global_stats
    """

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (origin, destination))
            result = cursor.fetchone()

    if not result or result[0] is None:
        raise ValueError("Unable to estimate the route duration from historical data.")

    route_observations = result[1] or 0
    source = "route_average" if route_observations > 0 else "global_average"

    return int(result[0]), source, int(route_observations)


def _build_weather_params(latitude: float, longitude: float, target_time: datetime) -> dict:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": target_time.strftime("%Y-%m-%d"),
        "end_date": target_time.strftime("%Y-%m-%d"),
        "timezone": "auto",
        "hourly": ",".join(WEATHER_FIELDS),
    }


def _select_weather_api_url(target_time: datetime) -> str:
    today = datetime.now().date()
    delta_days = (target_time.date() - today).days

    
    if -2 <= delta_days <= 16:
        return FORECAST_API_URL

    return ARCHIVE_API_URL


def _request_weather_with_retry(
    url: str,
    params: dict,
    latitude: float,
    longitude: float,
    rounded_label: str,
    max_attempts: int = 4,
) -> dict:
    backoff_seconds = [1, 2, 4, 8]

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, params=params, timeout=(5, 15))

        except requests.exceptions.Timeout as exc:
            if attempt == max_attempts - 1:
                raise UpstreamServiceError(
                    f"Weather API timeout for ({latitude}, {longitude}) at {rounded_label}."
                ) from exc

            time.sleep(backoff_seconds[min(attempt, len(backoff_seconds) - 1)])
            continue

        except requests.exceptions.RequestException as exc:
            if attempt == max_attempts - 1:
                raise UpstreamServiceError(
                    f"Weather API network error for ({latitude}, {longitude}) at {rounded_label}: {exc}"
                ) from exc

            time.sleep(backoff_seconds[min(attempt, len(backoff_seconds) - 1)])
            continue

        if response.status_code == 429:
            if attempt == max_attempts - 1:
                raise UpstreamServiceError(
                    f"Weather API rate limit reached for ({latitude}, {longitude}) at {rounded_label}. "
                    f"Response: {response.text}"
                )

            time.sleep(backoff_seconds[min(attempt, len(backoff_seconds) - 1)])
            continue

        if not response.ok:
            raise UpstreamServiceError(
                f"Weather API HTTP {response.status_code} for ({latitude}, {longitude}) "
                f"at {rounded_label} via {url}. Response: {response.text}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise UpstreamServiceError(
                f"Weather API returned invalid JSON for ({latitude}, {longitude}) at {rounded_label}. "
                f"Raw response: {response.text}"
            ) from exc

    raise UpstreamServiceError(
        f"Weather API failed after {max_attempts} attempts for ({latitude}, {longitude}) at {rounded_label}."
    )
@lru_cache(maxsize=64)
def _get_hourly_weather_cached(latitude: float, longitude: float, rounded_label: str) -> dict:
    target_time = datetime.strptime(rounded_label, "%Y-%m-%dT%H:%M")
    url = _select_weather_api_url(target_time)
    params = _build_weather_params(latitude, longitude, target_time)

    today = datetime.now().date()
    delta_days = (target_time.date() - today).days

    if url == FORECAST_API_URL and delta_days < 0:
        params["past_days"] = min(abs(delta_days), 92)

    return _request_weather_with_retry(
        url=url,
        params=params,
        latitude=latitude,
        longitude=longitude,
        rounded_label=rounded_label,
    )


def get_hourly_weather(latitude: float, longitude: float, flight_time: datetime) -> dict:
    rounded_time = _round_to_nearest_hour(flight_time)
    rounded_label = rounded_time.strftime("%Y-%m-%dT%H:%M")

    payload = _get_hourly_weather_cached(latitude, longitude, rounded_label)

    hourly = payload.get("hourly")
    if not hourly or "time" not in hourly:
        raise UpstreamServiceError(
            f"Weather API did not return hourly data for ({latitude}, {longitude}) at {rounded_label}. "
            f"Payload keys: {list(payload.keys())}"
        )

    weather_df = pd.DataFrame(hourly)
    if weather_df.empty:
        raise UpstreamServiceError(
            f"Weather API returned an empty hourly payload for ({latitude}, {longitude}) at {rounded_label}."
        )

    matching_rows = weather_df[weather_df["time"] == rounded_label]

    if matching_rows.empty:
        weather_df["time"] = pd.to_datetime(weather_df["time"])
        target_timestamp = pd.Timestamp(rounded_time)
        nearest_idx = (weather_df["time"] - target_timestamp).abs().idxmin()
        weather_row = weather_df.loc[nearest_idx]
        weather_timestamp = weather_row["time"].strftime("%Y-%m-%dT%H:%M")
    else:
        weather_row = matching_rows.iloc[0]
        weather_timestamp = rounded_label

    return {
        "temperature": float(weather_row["temperature_2m"]),
        "relative_humidity": int(weather_row["relative_humidity_2m"]),
        "dewpoint": float(weather_row["dew_point_2m"]),
        "apparent_temperature": float(weather_row["apparent_temperature"]),
        "precipitation": float(weather_row["precipitation"]),
        "wind_speed_10": float(weather_row["wind_speed_10m"]),
        "weather_timestamp": weather_timestamp,
    }


def build_feature_frame(origin: str, destination: str, scheduled_departure: datetime):
    origin_city = get_city_from_db(origin)
    destination_city = get_city_from_db(destination)

    estimated_duration, duration_source, route_observations = get_estimated_duration(
        origin, destination
    )

    local_departure = _ensure_naive_local_datetime(scheduled_departure)
    estimated_arrival = local_departure + timedelta(minutes=estimated_duration)

    origin_weather = get_hourly_weather(
        origin_city["latitude"],
        origin_city["longitude"],
        local_departure,
    )

    destination_weather = get_hourly_weather(
        destination_city["latitude"],
        destination_city["longitude"],
        estimated_arrival,
    )

    feature_row = {
        "estimated_duration": estimated_duration,
        "origin_temperature": origin_weather["temperature"],
        "origin_relative_humidity": origin_weather["relative_humidity"],
        "origin_dewpoint": origin_weather["dewpoint"],
        "origin_apparent_temperature": origin_weather["apparent_temperature"],
        "origin_precipitation": origin_weather["precipitation"],
        "origin_wind_speed_10": origin_weather["wind_speed_10"],
        "dest_temperature": destination_weather["temperature"],
        "dest_relative_humidity": destination_weather["relative_humidity"],
        "dest_dewpoint": destination_weather["dewpoint"],
        "dest_apparent_temperature": destination_weather["apparent_temperature"],
        "dest_precipitation": destination_weather["precipitation"],
        "dest_wind_speed_10": destination_weather["wind_speed_10"],
        "day_of_week": local_departure.isoweekday(),
        "month_flight": local_departure.month,
        "is_weekend": local_departure.isoweekday() in (6, 7),
        "origin_id_city": origin_city["id_city"],
        "dest_id_city": destination_city["id_city"],
        "route_code": f"{origin_city['id_city']}_{destination_city['id_city']}",
    }

    context = {
        "origin": origin_city,
        "destination": destination_city,
        "scheduled_departure": local_departure.isoformat(),
        "estimated_arrival_for_weather": estimated_arrival.isoformat(),
        "estimated_duration_minutes": estimated_duration,
        "estimated_duration_source": duration_source,
        "route_history_observations": route_observations,
        "origin_weather_timestamp": origin_weather["weather_timestamp"],
        "destination_weather_timestamp": destination_weather["weather_timestamp"],
        "assumption": "scheduled_departure is interpreted as local time at the origin airport.",
    }

    return pd.DataFrame([feature_row]), context


def predict_delay(origin: str, destination: str, scheduled_departure: datetime) -> dict:
    model, metadata = load_prediction_bundle()

    feature_frame, context = build_feature_frame(
        origin=origin,
        destination=destination,
        scheduled_departure=scheduled_departure,
    )

    raw_prediction = float(model.predict(feature_frame)[0])
    threshold = float(metadata.get("decision_threshold_minutes", 0.0))
    has_delay = raw_prediction >= threshold

    return {
        "status": "DELAY" if has_delay else "NO DELAY",
        "predicted_delay_minutes_raw": round(raw_prediction, 2),
        "predicted_delay_minutes": max(0, round(raw_prediction)) if has_delay else None,
        "model_name": metadata.get("model_name"),
        "decision_threshold_minutes": threshold,
        "prediction_rule": metadata.get("prediction_rule"),
        **context,
    }