"""Signal API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.signal import SignalDirectionUpdate, SignalFlagUpdate, SignalResponse
from backend.services import signal_service

router = APIRouter(prefix="/api/v1", tags=["signals"])


@router.post(
    "/transcripts/{transcript_id}/extract",
    response_model=list[SignalResponse],
    status_code=201,
)
def extract_signals(transcript_id: int, db: Session = Depends(get_db)):
    """Trigger LLM signal extraction from a transcript."""
    try:
        return signal_service.extract_signals(db, transcript_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/events/{event_id}/signals",
    response_model=list[SignalResponse],
)
def list_signals(event_id: int, db: Session = Depends(get_db)):
    """List all signals for an event."""
    return signal_service.list_signals(db, event_id)


@router.patch(
    "/signals/{signal_id}/flag",
    response_model=SignalResponse,
)
def flag_signal(
    signal_id: int, data: SignalFlagUpdate, db: Session = Depends(get_db)
):
    """Set user_flag (used_in_pricing or dismissed)."""
    try:
        return signal_service.flag_signal(db, signal_id, data.user_flag)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/signals/{signal_id}/direction",
    response_model=SignalResponse,
)
def set_direction(
    signal_id: int, data: SignalDirectionUpdate, db: Session = Depends(get_db)
):
    """Set signal direction (+1 favors home, -1 favors away)."""
    try:
        return signal_service.set_direction(db, signal_id, data.direction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
