"""Tests for transcript service."""

from datetime import date, datetime
from unittest.mock import patch

import pytest

from backend.schemas.event import EventCreate
from backend.schemas.slate import SlateCreate
from backend.services.event_service import create_event
from backend.services.slate_service import create_slate
from backend.services.transcript_service import (
    delete_transcript,
    get_transcript,
    ingest_from_text,
    ingest_from_url,
    list_transcripts,
)


def _setup_event(db):
    slate = create_slate(
        db, SlateCreate(name="Test", week_start=date(2025, 12, 1), week_end=date(2025, 12, 7))
    )
    return create_event(
        db,
        slate.id,
        EventCreate(
            home_team="Chiefs",
            away_team="Bills",
            sport="nfl",
            league="NFL",
            event_date=datetime(2025, 12, 5, 20, 0),
            market_type="moneyline",
        ),
    )


class TestIngestFromText:
    def test_stores_transcript(self, db):
        event = _setup_event(db)
        t = ingest_from_text(db, event.id, "Full transcript text here.")
        assert t.id is not None
        assert t.raw_text == "Full transcript text here."
        assert t.source_type == "manual"
        assert t.processed_at is not None

    def test_with_source_url(self, db):
        event = _setup_event(db)
        t = ingest_from_text(
            db, event.id, "Text", source_url="https://example.com"
        )
        assert t.source_url == "https://example.com"

    def test_raises_on_missing_event(self, db):
        with pytest.raises(ValueError, match="not found"):
            ingest_from_text(db, 999, "text")


class TestIngestFromUrl:
    @patch("yt_transcriber.pipeline.process_url_to_transcript")
    def test_calls_yt_transcriber(self, mock_transcribe, db):
        mock_transcribe.return_value = "Transcribed text from YouTube"
        event = _setup_event(db)
        t = ingest_from_url(db, event.id, "https://youtube.com/watch?v=abc123")
        assert t.raw_text == "Transcribed text from YouTube"
        assert t.source_type == "youtube"
        assert t.source_url == "https://youtube.com/watch?v=abc123"
        mock_transcribe.assert_called_once_with("https://youtube.com/watch?v=abc123")

    @patch("yt_transcriber.pipeline.process_url_to_transcript")
    def test_raises_on_transcription_failure(self, mock_transcribe, db):
        mock_transcribe.side_effect = RuntimeError("API error")
        event = _setup_event(db)
        with pytest.raises(ValueError, match="Transcription failed"):
            ingest_from_url(db, event.id, "https://youtube.com/watch?v=fail")

    def test_raises_on_missing_event(self, db):
        with pytest.raises(ValueError, match="not found"):
            ingest_from_url(db, 999, "https://youtube.com/watch?v=abc")


class TestGetTranscript:
    def test_returns_transcript(self, db):
        event = _setup_event(db)
        t = ingest_from_text(db, event.id, "Some text")
        assert get_transcript(db, t.id).raw_text == "Some text"

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError, match="not found"):
            get_transcript(db, 999)


class TestListTranscripts:
    def test_returns_all_for_event(self, db):
        event = _setup_event(db)
        ingest_from_text(db, event.id, "Text 1")
        ingest_from_text(db, event.id, "Text 2")
        assert len(list_transcripts(db, event.id)) == 2

    def test_empty(self, db):
        event = _setup_event(db)
        assert list_transcripts(db, event.id) == []


class TestDeleteTranscript:
    def test_deletes(self, db):
        event = _setup_event(db)
        t = ingest_from_text(db, event.id, "To delete")
        assert delete_transcript(db, t.id) is True
        with pytest.raises(ValueError):
            get_transcript(db, t.id)

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError):
            delete_transcript(db, 999)
