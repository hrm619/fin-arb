"""Tests for event service."""

from datetime import date, datetime

import pytest

from backend.schemas.event import EventCreate, EventUpdate
from backend.schemas.slate import SlateCreate
from backend.services.event_service import (
    create_event,
    delete_event,
    get_event,
    get_event_research,
    list_events,
    set_confidence_tier,
    update_event,
)
from backend.services.slate_service import create_slate


def _make_slate(db):
    return create_slate(
        db, SlateCreate(name="Test", week_start=date(2025, 12, 1), week_end=date(2025, 12, 7))
    )


def _event_data(**overrides):
    defaults = dict(
        home_team="Chiefs",
        away_team="Bills",
        sport="nfl",
        league="NFL",
        event_date=datetime(2025, 12, 5, 20, 0),
        market_type="moneyline",
    )
    defaults.update(overrides)
    return EventCreate(**defaults)


class TestCreateEvent:
    def test_creates_successfully(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        assert event.id is not None
        assert event.home_team == "Chiefs"
        assert event.slate_id == slate.id

    def test_raises_on_missing_slate(self, db):
        with pytest.raises(ValueError, match="not found"):
            create_event(db, 999, _event_data())

    def test_spread_fields(self, db):
        slate = _make_slate(db)
        event = create_event(
            db, slate.id, _event_data(market_type="spread", spread_value=-3.5)
        )
        assert event.spread_value == -3.5


class TestGetEvent:
    def test_returns_event(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        assert get_event(db, event.id).away_team == "Bills"

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError, match="not found"):
            get_event(db, 999)


class TestListEvents:
    def test_empty_slate(self, db):
        slate = _make_slate(db)
        assert list_events(db, slate.id) == []

    def test_returns_events_for_slate(self, db):
        slate = _make_slate(db)
        create_event(db, slate.id, _event_data())
        create_event(db, slate.id, _event_data(home_team="Eagles", away_team="Cowboys"))
        assert len(list_events(db, slate.id)) == 2

    def test_raises_on_missing_slate(self, db):
        with pytest.raises(ValueError):
            list_events(db, 999)


class TestUpdateEvent:
    def test_updates_fields(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        updated = update_event(db, event.id, EventUpdate(status="graded"))
        assert updated.status == "graded"

    def test_partial_update(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        updated = update_event(db, event.id, EventUpdate(home_team="Ravens"))
        assert updated.home_team == "Ravens"
        assert updated.away_team == "Bills"


class TestDeleteEvent:
    def test_deletes(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        assert delete_event(db, event.id) is True
        with pytest.raises(ValueError):
            get_event(db, event.id)


class TestSetConfidenceTier:
    def test_sets_tier(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        updated = set_confidence_tier(db, event.id, "high")
        assert updated.confidence_tier == "high"

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError):
            set_confidence_tier(db, 999, "low")


class TestGetEventResearch:
    def test_returns_aggregated_data(self, db):
        slate = _make_slate(db)
        event = create_event(db, slate.id, _event_data())
        research = get_event_research(db, event.id)
        assert research.event.id == event.id
        assert research.transcripts == []
        assert research.signals == []
        assert research.estimate is None
        assert research.market_lines == []
