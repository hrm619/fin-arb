"""Business logic for transcript operations."""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.models.transcript import Transcript
from backend.services.event_service import get_event

logger = logging.getLogger(__name__)


def ingest_from_url(db: Session, event_id: int, youtube_url: str) -> Transcript:
    """Download and transcribe a YouTube video, then store the transcript."""
    get_event(db, event_id)

    from yt_transcriber.pipeline import process_url_to_transcript

    try:
        raw_text = process_url_to_transcript(youtube_url)
    except Exception as e:
        logger.exception("Failed to transcribe URL: %s", youtube_url)
        raise ValueError(f"Transcription failed: {e}") from e

    transcript = Transcript(
        event_id=event_id,
        source_url=youtube_url,
        source_type="youtube",
        raw_text=raw_text,
        processed_at=datetime.now(tz=UTC),
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def ingest_from_text(
    db: Session, event_id: int, raw_text: str, source_url: str | None = None
) -> Transcript:
    """Store a pre-existing transcript directly."""
    get_event(db, event_id)
    transcript = Transcript(
        event_id=event_id,
        source_url=source_url,
        source_type="manual",
        raw_text=raw_text,
        processed_at=datetime.now(tz=UTC),
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def get_transcript(db: Session, transcript_id: int) -> Transcript:
    """Get a transcript by ID or raise."""
    transcript = db.get(Transcript, transcript_id)
    if not transcript:
        raise ValueError(f"Transcript {transcript_id} not found")
    return transcript


def list_transcripts(db: Session, event_id: int) -> list[Transcript]:
    """Return all transcripts for an event."""
    return list(
        db.query(Transcript)
        .filter(Transcript.event_id == event_id)
        .order_by(Transcript.created_at.desc())
        .all()
    )


def delete_transcript(db: Session, transcript_id: int) -> bool:
    """Delete a transcript."""
    transcript = get_transcript(db, transcript_id)
    db.delete(transcript)
    db.commit()
    return True
