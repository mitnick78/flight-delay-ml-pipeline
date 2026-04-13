from dotenv import load_dotenv

load_dotenv()

# ML Settings
TARGET_COLUMN = "arr_delay"

# Features to use for model training
NUMERICAL_FEATURES = [
    "estimated_duration",
    "origin_temperature", "origin_relative_humidity", "origin_dewpoint",
    "origin_apparent_temperature", "origin_precipitation", "origin_wind_speed_10",
    "dest_temperature", "dest_relative_humidity", "dest_dewpoint",
    "dest_apparent_temperature", "dest_precipitation", "dest_wind_speed_10"
]

CATEGORICAL_FEATURES = [
    "day_of_week", "month_flight", "is_weekend",
    "origin_id_city", "dest_id_city", "route_code"
]

# Random state for reproducibility
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Business rule for API responses:
# if the predicted delay is strictly below this threshold, we answer "NO DELAY".
DELAY_DECISION_THRESHOLD_MINUTES = 0.0
