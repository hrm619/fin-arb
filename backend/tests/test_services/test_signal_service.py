"""Tests for signal service."""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.schemas.event import EventCreate
from backend.schemas.slate import SlateCreate
from backend.services.event_service import create_event
from backend.services.signal_service import (
    extract_signals,
    flag_signal,
    list_signals,
    parse_llm_response,
    rank_signals,
)
from backend.services.slate_service import create_slate
from backend.services.transcript_service import ingest_from_text


def _setup_transcript(db):
    slate = create_slate(
        db, SlateCreate(name="Test", week_start=date(2025, 12, 1), week_end=date(2025, 12, 7))
    )
    event = create_event(
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
    transcript = ingest_from_text(db, event.id, "The Chiefs QB is questionable with an ankle injury.")
    return event, transcript


SAMPLE_LLM_RESPONSE = json.dumps([
    {
        "signal_type": "injury",
        "content": "Chiefs QB questionable with ankle injury",
        "relevance_score": 0.9,
        "timestamp_ref": "0:30",
    },
    {
        "signal_type": "sentiment",
        "content": "Analyst expects Bills to cover",
        "relevance_score": 0.6,
        "timestamp_ref": None,
    },
])


# --- parse_llm_response ---

class TestParseLlmResponse:
    def test_parses_valid_json(self):
        signals = parse_llm_response(SAMPLE_LLM_RESPONSE)
        assert len(signals) == 2
        assert signals[0].signal_type == "injury"
        assert signals[0].relevance_score == 0.9

    def test_handles_markdown_code_block(self):
        wrapped = f"```json\n{SAMPLE_LLM_RESPONSE}\n```"
        signals = parse_llm_response(wrapped)
        assert len(signals) == 2

    def test_returns_empty_on_invalid_json(self):
        assert parse_llm_response("not json at all") == []

    def test_returns_empty_on_non_array(self):
        assert parse_llm_response('{"key": "value"}') == []

    def test_skips_items_without_content(self):
        data = json.dumps([
            {"signal_type": "injury", "content": "", "relevance_score": 0.5},
            {"signal_type": "injury", "content": "Real signal", "relevance_score": 0.8},
        ])
        signals = parse_llm_response(data)
        assert len(signals) == 1


# --- rank_signals ---

class TestRankSignals:
    def test_sorts_by_relevance_desc(self):
        signals = parse_llm_response(SAMPLE_LLM_RESPONSE)
        ranked = rank_signals(signals)
        assert ranked[0].relevance_score >= ranked[1].relevance_score

    def test_empty_list(self):
        assert rank_signals([]) == []


# --- extract_signals (mocked Claude API) ---

class TestExtractSignals:
    @patch("backend.services.signal_service.anthropic")
    def test_extracts_and_stores(self, mock_anthropic_module, db):
        event, transcript = _setup_transcript(db)

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=SAMPLE_LLM_RESPONSE)]
        mock_client.messages.create.return_value = mock_message

        signals = extract_signals(db, transcript.id)
        assert len(signals) == 2
        assert signals[0].signal_type == "injury"
        assert signals[0].event_id == event.id
        assert signals[0].id is not None

    @patch("backend.services.signal_service.anthropic")
    def test_stores_ranked_order(self, mock_anthropic_module, db):
        _, transcript = _setup_transcript(db)

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=SAMPLE_LLM_RESPONSE)]
        mock_client.messages.create.return_value = mock_message

        signals = extract_signals(db, transcript.id)
        assert signals[0].relevance_score >= signals[1].relevance_score


# --- flag_signal ---

class TestFlagSignal:
    @patch("backend.services.signal_service.anthropic")
    def test_sets_flag(self, mock_anthropic_module, db):
        _, transcript = _setup_transcript(db)

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=SAMPLE_LLM_RESPONSE)]
        mock_client.messages.create.return_value = mock_message

        signals = extract_signals(db, transcript.id)
        flagged = flag_signal(db, signals[0].id, "used_in_pricing")
        assert flagged.user_flag == "used_in_pricing"

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError, match="not found"):
            flag_signal(db, 999, "dismissed")


# --- list_signals ---

class TestListSignals:
    @patch("backend.services.signal_service.anthropic")
    def test_returns_signals_for_event(self, mock_anthropic_module, db):
        event, transcript = _setup_transcript(db)

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=SAMPLE_LLM_RESPONSE)]
        mock_client.messages.create.return_value = mock_message

        extract_signals(db, transcript.id)
        signals = list_signals(db, event.id)
        assert len(signals) == 2

    def test_empty(self, db):
        event, _ = _setup_transcript(db)
        assert list_signals(db, event.id) == []
