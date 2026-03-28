"""Event API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.event import (
    ConfidenceTierUpdate,
    EventBatchCreate,
    EventCreate,
    EventResearchResponse,
    EventResponse,
    EventUpdate,
)
from backend.services import event_service

router = APIRouter(tags=["events"])


@router.get("/api/v1/slates/{slate_id}/events", response_model=list[EventResponse])
def list_events(slate_id: int, db: Session = Depends(get_db)):
    """List events on a slate."""
    try:
        return event_service.list_events(db, slate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/api/v1/slates/{slate_id}/events",
    response_model=EventResponse,
    status_code=201,
)
def create_event(slate_id: int, data: EventCreate, db: Session = Depends(get_db)):
    """Add an event to a slate."""
    try:
        return event_service.create_event(db, slate_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/api/v1/slates/{slate_id}/events/batch",
    response_model=list[EventResponse],
    status_code=201,
)
def create_events_batch(
    slate_id: int, data: EventBatchCreate, db: Session = Depends(get_db)
):
    """Add multiple events to a slate in one request."""
    try:
        return event_service.create_events_batch(db, slate_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/v1/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get full event detail."""
    try:
        return event_service.get_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/api/v1/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, data: EventUpdate, db: Session = Depends(get_db)):
    """Update event fields."""
    try:
        return event_service.update_event(db, event_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/api/v1/events/{event_id}/confidence", response_model=EventResponse
)
def set_confidence_tier(
    event_id: int, data: ConfidenceTierUpdate, db: Session = Depends(get_db)
):
    """Set confidence tier on an event."""
    try:
        return event_service.set_confidence_tier(db, event_id, data.confidence_tier)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/api/v1/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Remove an event."""
    try:
        event_service.delete_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/api/v1/events/{event_id}/research", response_model=EventResearchResponse
)
def get_event_research(event_id: int, db: Session = Depends(get_db)):
    """Aggregate all research for an event."""
    try:
        return event_service.get_event_research(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
