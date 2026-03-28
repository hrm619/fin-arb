"""Tests for estimate service."""

from datetime import date, datetime

import pytest

from backend.schemas.estimate import EstimateCreate
from backend.schemas.event import EventCreate
from backend.schemas.slate import SlateCreate
from backend.services.estimate_service import (
    get_estimate,
    is_locked,
    submit_estimate,
)
from backend.services.event_service import create_event
from backend.services.slate_service import create_slate


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


class TestSubmitEstimate:
    def test_creates_estimate(self, db):
        event = _setup_event(db)
        est = submit_estimate(db, event.id, EstimateCreate(probability_pct=60.0))
        assert est.id is not None
        assert est.probability_pct == 60.0
        assert est.locked_at is not None

    def test_computes_american_odds(self, db):
        event = _setup_event(db)
        est = submit_estimate(db, event.id, EstimateCreate(probability_pct=70.0))
        assert est.american_odds == -233

    def test_computes_decimal_odds(self, db):
        event = _setup_event(db)
        est = submit_estimate(db, event.id, EstimateCreate(probability_pct=25.0))
        assert est.decimal_odds == 4.0

    def test_saves_note(self, db):
        event = _setup_event(db)
        est = submit_estimate(
            db, event.id, EstimateCreate(probability_pct=55.0, note="Chiefs at home")
        )
        assert est.note == "Chiefs at home"

    def test_rejects_duplicate(self, db):
        event = _setup_event(db)
        submit_estimate(db, event.id, EstimateCreate(probability_pct=60.0))
        with pytest.raises(ValueError, match="already exists and is locked"):
            submit_estimate(db, event.id, EstimateCreate(probability_pct=65.0))

    def test_raises_on_missing_event(self, db):
        with pytest.raises(ValueError, match="not found"):
            submit_estimate(db, 999, EstimateCreate(probability_pct=50.0))


class TestGetEstimate:
    def test_returns_estimate(self, db):
        event = _setup_event(db)
        submit_estimate(db, event.id, EstimateCreate(probability_pct=60.0))
        est = get_estimate(db, event.id)
        assert est.probability_pct == 60.0

    def test_raises_when_none(self, db):
        event = _setup_event(db)
        with pytest.raises(ValueError, match="No estimate"):
            get_estimate(db, event.id)


class TestIsLocked:
    def test_true_after_submit(self, db):
        event = _setup_event(db)
        submit_estimate(db, event.id, EstimateCreate(probability_pct=60.0))
        assert is_locked(db, event.id) is True

    def test_false_before_submit(self, db):
        event = _setup_event(db)
        assert is_locked(db, event.id) is False
