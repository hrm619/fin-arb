"""Business logic for user estimate operations."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.models.estimate import UserEstimate
from backend.schemas.estimate import EstimateCreate
from backend.services.event_service import get_event
from backend.utils.odds_converter import pct_to_american, pct_to_decimal


def submit_estimate(db: Session, event_id: int, data: EstimateCreate) -> UserEstimate:
    """Submit a probability estimate for an event. Locks immediately on creation."""
    get_event(db, event_id)
    existing = _get_estimate_or_none(db, event_id)
    if existing is not None:
        raise ValueError(f"Estimate for event {event_id} already exists and is locked")

    estimate = UserEstimate(
        event_id=event_id,
        probability_pct=data.probability_pct,
        american_odds=pct_to_american(data.probability_pct),
        decimal_odds=pct_to_decimal(data.probability_pct),
        note=data.note,
        locked_at=datetime.now(tz=UTC),
    )
    db.add(estimate)
    db.commit()
    db.refresh(estimate)
    return estimate


def get_estimate(db: Session, event_id: int) -> UserEstimate:
    """Get the estimate for an event or raise."""
    estimate = _get_estimate_or_none(db, event_id)
    if estimate is None:
        raise ValueError(f"No estimate for event {event_id}")
    return estimate


def is_locked(db: Session, event_id: int) -> bool:
    """Return True if an estimate exists (all estimates are locked on submit)."""
    return _get_estimate_or_none(db, event_id) is not None


def _get_estimate_or_none(db: Session, event_id: int) -> UserEstimate | None:
    """Internal helper to fetch estimate without raising."""
    return (
        db.query(UserEstimate)
        .filter(UserEstimate.event_id == event_id)
        .first()
    )
