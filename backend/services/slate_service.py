"""Business logic for slate operations."""

from sqlalchemy.orm import Session

from backend.models.slate import Slate
from backend.schemas.slate import SlateCreate, SlateUpdate


def create_slate(db: Session, data: SlateCreate) -> Slate:
    """Create a new slate."""
    slate = Slate(**data.model_dump())
    db.add(slate)
    db.commit()
    db.refresh(slate)
    return slate


def get_slate(db: Session, slate_id: int) -> Slate:
    """Get a slate by ID or raise."""
    slate = db.get(Slate, slate_id)
    if not slate:
        raise ValueError(f"Slate {slate_id} not found")
    return slate


def list_slates(db: Session) -> list[Slate]:
    """Return all slates ordered by creation date descending."""
    return list(db.query(Slate).order_by(Slate.created_at.desc()).all())


def update_slate(db: Session, slate_id: int, data: SlateUpdate) -> Slate:
    """Update slate fields."""
    slate = get_slate(db, slate_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(slate, field, value)
    db.commit()
    db.refresh(slate)
    return slate


def delete_slate(db: Session, slate_id: int) -> bool:
    """Delete a slate and its cascade children."""
    slate = get_slate(db, slate_id)
    db.delete(slate)
    db.commit()
    return True
