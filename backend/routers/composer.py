"""Estimate composition API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.composer import SuggestedEstimateResponse
from backend.schemas.structural_priors import StructuralPriorsResponse
from backend.services import composer as composer_service
from backend.services.structural_priors import get_applicable_edges

router = APIRouter(prefix="/api/v1", tags=["composer"])


@router.get(
    "/events/{event_id}/suggested-estimate",
    response_model=SuggestedEstimateResponse,
)
def get_suggested_estimate(event_id: int, db: Session = Depends(get_db)):
    """Get or generate a suggested estimate for an event."""
    existing = composer_service.get_suggested_estimate(db, event_id)
    if existing and existing.decomposition_json:
        # Return cached version — use POST to regenerate
        try:
            return composer_service.compose_estimate(db, event_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    try:
        return composer_service.compose_estimate(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/events/{event_id}/suggested-estimate",
    response_model=SuggestedEstimateResponse,
)
def regenerate_suggested_estimate(event_id: int, db: Session = Depends(get_db)):
    """Force regeneration of a suggested estimate."""
    try:
        return composer_service.compose_estimate(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/events/{event_id}/structural-priors",
    response_model=StructuralPriorsResponse,
)
def get_structural_priors(event_id: int, db: Session = Depends(get_db)):
    """Return applicable structural priors for an event."""
    from backend.services.event_service import get_event

    try:
        event = get_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    edges = get_applicable_edges(event.home_team, event.away_team, season=2024)
    total = sum(e.edge_magnitude for e in edges)

    return StructuralPriorsResponse(
        event_id=event_id,
        edges=edges,
        total_structural_adjustment=round(total, 4),
    )
