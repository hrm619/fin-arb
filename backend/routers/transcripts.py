"""Transcript API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.transcript import (
    TranscriptIngestText,
    TranscriptIngestURL,
    TranscriptResponse,
)
from backend.services import transcript_service

router = APIRouter(prefix="/api/v1", tags=["transcripts"])


@router.post(
    "/events/{event_id}/transcripts/url",
    response_model=TranscriptResponse,
    status_code=201,
)
def ingest_from_url(
    event_id: int, data: TranscriptIngestURL, db: Session = Depends(get_db)
):
    """Ingest a transcript from a YouTube URL."""
    try:
        return transcript_service.ingest_from_url(db, event_id, data.source_url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/events/{event_id}/transcripts",
    response_model=TranscriptResponse,
    status_code=201,
)
def ingest_from_text(
    event_id: int, data: TranscriptIngestText, db: Session = Depends(get_db)
):
    """Ingest a transcript from raw text."""
    try:
        return transcript_service.ingest_from_text(
            db, event_id, data.raw_text, data.source_url
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/events/{event_id}/transcripts",
    response_model=list[TranscriptResponse],
)
def list_transcripts(event_id: int, db: Session = Depends(get_db)):
    """List transcripts for an event."""
    return transcript_service.list_transcripts(db, event_id)


@router.get(
    "/transcripts/{transcript_id}",
    response_model=TranscriptResponse,
)
def get_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """Get full transcript text."""
    try:
        return transcript_service.get_transcript(db, transcript_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/transcripts/{transcript_id}", status_code=204)
def delete_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """Remove a transcript."""
    try:
        transcript_service.delete_transcript(db, transcript_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
