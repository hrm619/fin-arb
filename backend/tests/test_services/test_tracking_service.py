"""Tests for tracking service."""

from datetime import UTC, date, datetime

import pytest

from backend.schemas.estimate import EstimateCreate
from backend.schemas.event import EventCreate
from backend.schemas.outcome import OutcomeCreate
from backend.schemas.slate import SlateCreate
from backend.services.estimate_service import submit_estimate
from backend.services.event_service import create_event
from backend.services.line_service import store_lines
from backend.services.slate_service import create_slate
from backend.services.tracking_service import (
    compute_edge_by_dimension,
    compute_hit_rate,
    compute_roi,
    export_to_csv,
    get_outcome,
    get_summary,
    grade_event,
)


def _setup_slate(db):
    return create_slate(
        db, SlateCreate(name="Test", week_start=date(2025, 12, 1), week_end=date(2025, 12, 7))
    )


def _add_event(db, slate_id, home="Chiefs", away="Bills", sport="nfl", market_type="moneyline", confidence_tier=None):
    return create_event(
        db,
        slate_id,
        EventCreate(
            home_team=home, away_team=away, sport=sport, league="NFL",
            event_date=datetime(2025, 12, 5, 20, 0), market_type=market_type,
            confidence_tier=confidence_tier,
        ),
    )


def _grade(db, event_id, result="win", score=None, notes=None):
    return grade_event(db, event_id, OutcomeCreate(result=result, actual_score=score, notes=notes))


class TestGradeEvent:
    def test_grades_successfully(self, db):
        slate = _setup_slate(db)
        event = _add_event(db, slate.id)
        outcome = _grade(db, event.id, "win", "24-17")
        assert outcome.id is not None
        assert outcome.result == "win"
        assert outcome.actual_score == "24-17"
        assert outcome.graded_by == "user"

    def test_sets_event_status_graded(self, db):
        from backend.services.event_service import get_event
        slate = _setup_slate(db)
        event = _add_event(db, slate.id)
        _grade(db, event.id)
        assert get_event(db, event.id).status == "graded"

    def test_rejects_duplicate(self, db):
        slate = _setup_slate(db)
        event = _add_event(db, slate.id)
        _grade(db, event.id)
        with pytest.raises(ValueError, match="already graded"):
            _grade(db, event.id, "loss")


class TestGetOutcome:
    def test_returns_outcome(self, db):
        slate = _setup_slate(db)
        event = _add_event(db, slate.id)
        _grade(db, event.id, "loss")
        assert get_outcome(db, event.id).result == "loss"

    def test_raises_when_none(self, db):
        slate = _setup_slate(db)
        event = _add_event(db, slate.id)
        with pytest.raises(ValueError, match="No outcome"):
            get_outcome(db, event.id)


class TestComputeHitRate:
    def test_all_wins(self, db):
        slate = _setup_slate(db)
        for _ in range(3):
            e = _add_event(db, slate.id)
            _grade(db, e.id, "win")
        assert compute_hit_rate(db) == 1.0

    def test_all_losses(self, db):
        slate = _setup_slate(db)
        for _ in range(3):
            e = _add_event(db, slate.id)
            _grade(db, e.id, "loss")
        assert compute_hit_rate(db) == 0.0

    def test_mixed(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        e2 = _add_event(db, slate.id, home="Eagles", away="Cowboys")
        _grade(db, e1.id, "win")
        _grade(db, e2.id, "loss")
        assert compute_hit_rate(db) == 0.5

    def test_excludes_pushes(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        e2 = _add_event(db, slate.id, home="Eagles", away="Cowboys")
        _grade(db, e1.id, "win")
        _grade(db, e2.id, "push")
        assert compute_hit_rate(db) == 1.0

    def test_filter_by_sport(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id, sport="nfl")
        e2 = _add_event(db, slate.id, home="Lakers", away="Celtics", sport="nba")
        _grade(db, e1.id, "win")
        _grade(db, e2.id, "loss")
        assert compute_hit_rate(db, sport="nfl") == 1.0
        assert compute_hit_rate(db, sport="nba") == 0.0

    def test_empty(self, db):
        assert compute_hit_rate(db) == 0.0


class TestComputeRoi:
    def test_positive_roi(self, db):
        slate = _setup_slate(db)
        for _ in range(3):
            e = _add_event(db, slate.id)
            _grade(db, e.id, "win")
        assert compute_roi(db) == 1.0

    def test_negative_roi(self, db):
        slate = _setup_slate(db)
        for _ in range(3):
            e = _add_event(db, slate.id)
            _grade(db, e.id, "loss")
        assert compute_roi(db) == -1.0

    def test_break_even(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        e2 = _add_event(db, slate.id, home="Eagles", away="Cowboys")
        _grade(db, e1.id, "win")
        _grade(db, e2.id, "loss")
        assert compute_roi(db) == 0.0

    def test_empty(self, db):
        assert compute_roi(db) == 0.0


class TestGetSummary:
    def test_aggregates(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        e2 = _add_event(db, slate.id, home="Eagles", away="Cowboys")
        e3 = _add_event(db, slate.id, home="Ravens", away="Bengals")
        _grade(db, e1.id, "win")
        _grade(db, e2.id, "loss")
        _grade(db, e3.id, "push")
        summary = get_summary(db)
        assert summary.total_graded == 3
        assert summary.wins == 1
        assert summary.losses == 1
        assert summary.pushes == 1
        assert summary.hit_rate == 0.5

    def test_empty(self, db):
        summary = get_summary(db)
        assert summary.total_graded == 0
        assert summary.hit_rate == 0.0


class TestEdgeByDimension:
    def test_by_sport(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id, sport="nfl")
        e2 = _add_event(db, slate.id, home="Lakers", away="Celtics", sport="nba")
        _grade(db, e1.id, "win")
        _grade(db, e2.id, "loss")
        breakdowns = compute_edge_by_dimension(db, "sport")
        assert len(breakdowns) == 2
        nfl = [b for b in breakdowns if b.group == "nfl"][0]
        assert nfl.hit_rate == 1.0
        nba = [b for b in breakdowns if b.group == "nba"][0]
        assert nba.hit_rate == 0.0

    def test_includes_avg_edge(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id, sport="nfl")
        submit_estimate(db, e1.id, EstimateCreate(probability_pct=65.0))
        store_lines(db, e1.id, [{
            "event_id": e1.id, "source": "dk", "market_key": "h2h",
            "implied_prob_pct": 50.0, "american_odds": None,
            "decimal_odds": 2.0, "fetched_at": datetime.now(tz=UTC),
            "raw_response": None,
        }])
        _grade(db, e1.id, "win")
        breakdowns = compute_edge_by_dimension(db, "sport")
        nfl = breakdowns[0]
        assert nfl.avg_edge == pytest.approx(0.15, abs=0.01)

    def test_empty(self, db):
        assert compute_edge_by_dimension(db, "sport") == []


class TestExportToCsv:
    def test_exports_rows(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        _grade(db, e1.id, "win", "24-17", "Good pick")
        csv_str = export_to_csv(db)
        assert "Chiefs" in csv_str
        assert "win" in csv_str
        assert "24-17" in csv_str
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # header + 1 row

    def test_empty(self, db):
        csv_str = export_to_csv(db)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # header only
