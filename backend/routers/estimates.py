"""User estimate API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.estimate import EstimateCreate, EstimateResponse
from backend.services import estimate_service

router = APIRouter(prefix="/api/v1", tags=["estimates"])


@router.post(
    "/events/{event_id}/estimate",
    response_model=EstimateResponse,
    status_code=201,
)
def submit_estimate(
    event_id: int, data: EstimateCreate, db: Session = Depends(get_db)
):
    """Submit a probability estimate (locks on submit)."""
    try:
        return estimate_service.submit_estimate(db, event_id, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/events/{event_id}/estimate",
    response_model=EstimateResponse,
)
def get_estimate(event_id: int, db: Session = Depends(get_db)):
    """Get the current estimate for an event."""
    try:
        return estimate_service.get_estimate(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
