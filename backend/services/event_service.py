"""Business logic for event operations."""

from sqlalchemy.orm import Session

from backend.models.event import Event
from backend.schemas.event import EventCreate, EventResearchResponse, EventResponse, EventUpdate
from backend.services.slate_service import get_slate


def create_event(db: Session, slate_id: int, data: EventCreate) -> Event:
    """Create a new event on a slate."""
    get_slate(db, slate_id)  # ensure slate exists
    event = Event(slate_id=slate_id, **data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Event:
    """Get an event by ID or raise."""
    event = db.get(Event, event_id)
    if not event:
        raise ValueError(f"Event {event_id} not found")
    return event


def list_events(db: Session, slate_id: int) -> list[Event]:
    """Return all events for a slate."""
    get_slate(db, slate_id)  # ensure slate exists
    return list(
        db.query(Event)
        .filter(Event.slate_id == slate_id)
        .order_by(Event.event_date)
        .all()
    )


def update_event(db: Session, event_id: int, data: EventUpdate) -> Event:
    """Update event fields."""
    event = get_event(db, event_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int) -> bool:
    """Delete an event."""
    event = get_event(db, event_id)
    db.delete(event)
    db.commit()
    return True


def set_confidence_tier(db: Session, event_id: int, tier: str) -> Event:
    """Set the confidence tier on an event."""
    event = get_event(db, event_id)
    event.confidence_tier = tier
    db.commit()
    db.refresh(event)
    return event


def get_event_research(db: Session, event_id: int) -> EventResearchResponse:
    """Aggregate all research data for an event."""
    event = get_event(db, event_id)
    return EventResearchResponse(
        event=EventResponse.model_validate(event),
        transcripts=[t.__dict__ for t in event.transcripts],
        signals=[s.__dict__ for s in event.signals],
        estimate=event.estimate.__dict__ if event.estimate else None,
        market_lines=[ml.__dict__ for ml in event.market_lines],
    )
