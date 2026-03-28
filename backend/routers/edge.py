"""Edge ranking API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.edge import RankedEvent
from backend.schemas.market_line import ArbOpportunity
from backend.services import edge_service

router = APIRouter(prefix="/api/v1/slates", tags=["edge"])


@router.get("/{slate_id}/edge", response_model=list[RankedEvent])
def get_edge_ranking(slate_id: int, db: Session = Depends(get_db)):
    """Ranked edge table for a full slate."""
    try:
        return edge_service.rank_slate(db, slate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{slate_id}/shortlist", response_model=list[RankedEvent])
def get_shortlist(slate_id: int, db: Session = Depends(get_db)):
    """Top N events by edge x confidence."""
    try:
        return edge_service.get_shortlist(db, slate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{slate_id}/arb", response_model=list[ArbOpportunity])
def get_arb_opportunities(slate_id: int, db: Session = Depends(get_db)):
    """Cross-market arb opportunities across all events on a slate."""
    try:
        return edge_service.get_arb_opportunities(db, slate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
