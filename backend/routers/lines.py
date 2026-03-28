"""Market lines API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.market_line import ArbOpportunity, MarketLineResponse
from backend.services import line_service

router = APIRouter(prefix="/api/v1", tags=["lines"])


@router.post(
    "/events/{event_id}/lines/fetch",
    response_model=list[MarketLineResponse],
)
async def fetch_lines(event_id: int, db: Session = Depends(get_db)):
    """Trigger on-demand line fetch from external sources."""
    try:
        return await line_service.fetch_lines(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/events/{event_id}/lines",
    response_model=list[MarketLineResponse],
)
def get_lines(event_id: int, db: Session = Depends(get_db)):
    """Get all stored lines for an event."""
    return line_service.get_lines(db, event_id)


@router.get(
    "/events/{event_id}/lines/arb",
    response_model=list[ArbOpportunity],
)
def get_arb_opportunities(event_id: int, db: Session = Depends(get_db)):
    """Get cross-market arb opportunities for an event."""
    return line_service.detect_arb_opportunities(db, event_id)
