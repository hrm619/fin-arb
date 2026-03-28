"""Slate API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.slate import (
    SlateCreate,
    SlateDetailResponse,
    SlateResponse,
    SlateUpdate,
)
from backend.services import slate_service

router = APIRouter(prefix="/api/v1/slates", tags=["slates"])


@router.get("", response_model=list[SlateResponse])
def list_slates(db: Session = Depends(get_db)):
    """List all slates."""
    return slate_service.list_slates(db)


@router.post("", response_model=SlateResponse, status_code=201)
def create_slate(data: SlateCreate, db: Session = Depends(get_db)):
    """Create a new slate."""
    return slate_service.create_slate(db, data)


@router.get("/{slate_id}", response_model=SlateDetailResponse)
def get_slate(slate_id: int, db: Session = Depends(get_db)):
    """Get a slate with its events."""
    try:
        return slate_service.get_slate(db, slate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{slate_id}", response_model=SlateResponse)
def update_slate(slate_id: int, data: SlateUpdate, db: Session = Depends(get_db)):
    """Update slate metadata."""
    try:
        return slate_service.update_slate(db, slate_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{slate_id}", status_code=204)
def delete_slate(slate_id: int, db: Session = Depends(get_db)):
    """Delete a slate."""
    try:
        slate_service.delete_slate(db, slate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
