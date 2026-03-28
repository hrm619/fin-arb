"""Tracking API routes."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.outcome import (
    EdgeBreakdown,
    OutcomeCreate,
    OutcomeResponse,
    TrackingSummary,
)
from backend.services import tracking_service

router = APIRouter(prefix="/api/v1", tags=["tracking"])


@router.post(
    "/events/{event_id}/outcome",
    response_model=OutcomeResponse,
    status_code=201,
)
def grade_event(event_id: int, data: OutcomeCreate, db: Session = Depends(get_db)):
    """Grade an event result."""
    try:
        return tracking_service.grade_event(db, event_id, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/tracking/summary", response_model=TrackingSummary)
def get_summary(db: Session = Depends(get_db)):
    """Aggregate performance metrics."""
    return tracking_service.get_summary(db)


@router.get(
    "/tracking/breakdown/{dimension}",
    response_model=list[EdgeBreakdown],
)
def get_breakdown(dimension: str, db: Session = Depends(get_db)):
    """Edge breakdown by sport, market_type, or confidence_tier."""
    if dimension not in ("sport", "market_type", "confidence_tier"):
        raise HTTPException(status_code=400, detail="Invalid dimension")
    return tracking_service.compute_edge_by_dimension(db, dimension)


@router.get("/tracking/export")
def export_csv(db: Session = Depends(get_db)):
    """CSV export of all graded events."""
    csv_str = tracking_service.export_to_csv(db)
    return PlainTextResponse(content=csv_str, media_type="text/csv")
