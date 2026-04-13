from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from delay_prediction import UpstreamServiceError, predict_delay

router = APIRouter(prefix="/predict", tags=["predict"])
logger = logging.getLogger("flight_predictor")
logging.basicConfig(level=logging.INFO)


class FlightInput(BaseModel):
    origin: str
    destination: str
    scheduled_departure: datetime


@router.post("/")
def predict(flight: FlightInput):
    origin = flight.origin.upper()
    destination = flight.destination.upper()

    logger.info(
        "Prediction request received origin=%s destination=%s scheduled_departure=%s",
        origin,
        destination,
        flight.scheduled_departure,
    )

    try:
        result = predict_delay(
            origin=origin,
            destination=destination,
            scheduled_departure=flight.scheduled_departure,
        )

        return result

    except FileNotFoundError as exc:
        logger.exception("Prediction failed because model artifact is unavailable")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    except ValueError as exc:
        logger.exception("Prediction failed with validation/business error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except UpstreamServiceError as exc:
        logger.exception("Prediction failed because weather provider is unavailable")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    except Exception as exc:
        logger.exception("Prediction failed with unexpected internal error")
        raise HTTPException(status_code=500, detail="Internal server error") from exc