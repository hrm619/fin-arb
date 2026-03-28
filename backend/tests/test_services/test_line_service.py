"""Tests for line service (database operations, no live API calls)."""

from datetime import UTC, date, datetime

import pytest

from backend.schemas.slate import SlateCreate
from backend.schemas.event import EventCreate
from backend.services.event_service import create_event
from backend.services.line_service import (
    detect_arb_opportunities,
    get_best_line,
    get_lines,
    store_lines,
)
from backend.services.slate_service import create_slate


def _setup_event(db):
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
    return event


def _line_dict(
    event_id, source, implied_prob_pct,
    american_odds=None, decimal_odds=None, outcome_name=None,
):
    return {
        "event_id": event_id,
        "source": source,
        "outcome_name": outcome_name,
        "market_key": "h2h",
        "implied_prob_pct": implied_prob_pct,
        "american_odds": american_odds,
        "decimal_odds": decimal_odds,
        "fetched_at": datetime.now(tz=UTC),
        "raw_response": None,
    }


class TestStoreLines:
    def test_stores_lines(self, db):
        event = _setup_event(db)
        lines = store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 60.0, -150, 1.67),
            _line_dict(event.id, "fanduel", 58.0, -138, 1.72),
        ])
        assert len(lines) == 2
        assert lines[0].id is not None

    def test_empty_list(self, db):
        event = _setup_event(db)
        assert store_lines(db, event.id, []) == []


class TestGetLines:
    def test_returns_stored_lines(self, db):
        event = _setup_event(db)
        store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 60.0),
            _line_dict(event.id, "fanduel", 58.0),
        ])
        assert len(get_lines(db, event.id)) == 2

    def test_empty_when_none(self, db):
        event = _setup_event(db)
        assert get_lines(db, event.id) == []


class TestGetBestLine:
    def test_returns_lowest_implied_prob(self, db):
        event = _setup_event(db)
        store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 60.0),
            _line_dict(event.id, "fanduel", 55.0),
            _line_dict(event.id, "betmgm", 58.0),
        ])
        best = get_best_line(db, event.id)
        assert best is not None
        assert best.source == "fanduel"
        assert best.implied_prob_pct == 55.0

    def test_returns_none_when_empty(self, db):
        event = _setup_event(db)
        assert get_best_line(db, event.id) is None


class TestDetectArbOpportunities:
    def test_finds_arb(self, db):
        event = _setup_event(db)
        # Chiefs at 45% (DK) + Bills at 48% (FD) = 93% < 97% threshold
        store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 45.0, outcome_name="Chiefs"),
            _line_dict(event.id, "fanduel", 48.0, outcome_name="Bills"),
        ])
        arbs = detect_arb_opportunities(db, event.id)
        assert len(arbs) == 1
        assert arbs[0].arb_edge_pct > 0

    def test_no_arb_when_probs_high(self, db):
        event = _setup_event(db)
        store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 55.0, outcome_name="Chiefs"),
            _line_dict(event.id, "fanduel", 53.0, outcome_name="Bills"),
        ])
        arbs = detect_arb_opportunities(db, event.id)
        assert len(arbs) == 0

    def test_skips_same_source(self, db):
        event = _setup_event(db)
        store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 45.0, outcome_name="Chiefs"),
            _line_dict(event.id, "draftkings", 48.0, outcome_name="Bills"),
        ])
        arbs = detect_arb_opportunities(db, event.id)
        assert len(arbs) == 0

    def test_skips_same_outcome(self, db):
        event = _setup_event(db)
        # Same outcome from different books — not an arb
        store_lines(db, event.id, [
            _line_dict(event.id, "draftkings", 45.0, outcome_name="Chiefs"),
            _line_dict(event.id, "fanduel", 43.0, outcome_name="Chiefs"),
        ])
        arbs = detect_arb_opportunities(db, event.id)
        assert len(arbs) == 0

    def test_empty_lines(self, db):
        event = _setup_event(db)
        assert detect_arb_opportunities(db, event.id) == []
