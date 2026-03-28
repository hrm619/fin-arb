"""Tests for edge service."""

from datetime import UTC, date, datetime

import pytest

from backend.schemas.estimate import EstimateCreate
from backend.schemas.event import EventCreate
from backend.schemas.slate import SlateCreate
from backend.services.edge_service import (
    compute_edge,
    compute_kelly,
    confidence_weight,
    get_arb_opportunities,
    get_shortlist,
    rank_slate,
    weighted_score,
)
from backend.services.estimate_service import submit_estimate
from backend.services.event_service import create_event
from backend.services.line_service import store_lines
from backend.services.slate_service import create_slate


def _setup_slate(db):
    return create_slate(
        db, SlateCreate(name="Test", week_start=date(2025, 12, 1), week_end=date(2025, 12, 7))
    )


def _add_event(db, slate_id, home="Chiefs", away="Bills", confidence_tier=None):
    return create_event(
        db,
        slate_id,
        EventCreate(
            home_team=home,
            away_team=away,
            sport="nfl",
            league="NFL",
            event_date=datetime(2025, 12, 5, 20, 0),
            market_type="moneyline",
            confidence_tier=confidence_tier,
        ),
    )


def _add_estimate(db, event_id, prob_pct):
    return submit_estimate(db, event_id, EstimateCreate(probability_pct=prob_pct))


def _add_line(db, event_id, source, implied_prob_pct, decimal_odds, outcome_name="Chiefs"):
    store_lines(db, event_id, [{
        "event_id": event_id,
        "source": source,
        "outcome_name": outcome_name,
        "market_key": "h2h",
        "implied_prob_pct": implied_prob_pct,
        "american_odds": None,
        "decimal_odds": decimal_odds,
        "fetched_at": datetime.now(tz=UTC),
        "raw_response": None,
    }])


# --- Pure function tests ---

class TestComputeEdge:
    def test_positive_edge(self):
        assert compute_edge(60, 50) == pytest.approx(0.10, abs=0.001)

    def test_negative_edge(self):
        assert compute_edge(40, 50) == pytest.approx(-0.10, abs=0.001)


class TestComputeKelly:
    def test_returns_stake(self):
        stake = compute_kelly(0.10, 2.0, 1000.0)
        assert stake > 0

    def test_zero_edge(self):
        assert compute_kelly(0.0, 2.0, 1000.0) == 0.0


class TestConfidenceWeight:
    def test_high(self):
        assert confidence_weight("high") == 1.0

    def test_medium(self):
        assert confidence_weight("medium") == 0.7

    def test_low(self):
        assert confidence_weight("low") == 0.4

    def test_none(self):
        assert confidence_weight(None) == 0.5


class TestWeightedScore:
    def test_high_edge_high_confidence(self):
        assert weighted_score(0.10, "high") == pytest.approx(0.10, abs=0.001)

    def test_edge_with_medium(self):
        assert weighted_score(0.10, "medium") == pytest.approx(0.07, abs=0.001)


# --- Slate ranking tests ---

class TestRankSlate:
    def test_ranks_by_weighted_score(self, db):
        slate = _setup_slate(db)

        e1 = _add_event(db, slate.id, "Chiefs", "Bills", confidence_tier="high")
        _add_estimate(db, e1.id, 65.0)
        _add_line(db, e1.id, "draftkings", 50.0, 2.0)

        e2 = _add_event(db, slate.id, "Eagles", "Cowboys", confidence_tier="medium")
        _add_estimate(db, e2.id, 70.0)
        _add_line(db, e2.id, "fanduel", 50.0, 2.0, outcome_name="Eagles")

        ranked = rank_slate(db, slate.id)
        assert len(ranked) == 2
        # e2 has higher raw edge (0.20) but medium weight (0.7) → 0.14
        # e1 has raw edge (0.15) with high weight (1.0) → 0.15
        assert ranked[0].event_id == e1.id
        assert ranked[1].event_id == e2.id

    def test_skips_events_without_estimate(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        _add_line(db, e1.id, "draftkings", 50.0, 2.0)
        assert rank_slate(db, slate.id) == []

    def test_skips_events_without_lines(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        _add_estimate(db, e1.id, 65.0)
        assert rank_slate(db, slate.id) == []

    def test_skips_events_below_threshold(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id)
        _add_estimate(db, e1.id, 51.0)  # only 1% edge, below 3% threshold
        _add_line(db, e1.id, "draftkings", 50.0, 2.0)
        assert rank_slate(db, slate.id) == []

    def test_empty_slate(self, db):
        slate = _setup_slate(db)
        assert rank_slate(db, slate.id) == []

    def test_ranked_event_fields(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id, "Chiefs", "Bills", confidence_tier="high")
        _add_estimate(db, e1.id, 65.0)
        _add_line(db, e1.id, "draftkings", 50.0, 2.0)

        ranked = rank_slate(db, slate.id)
        r = ranked[0]
        assert r.home_team == "Chiefs"
        assert r.away_team == "Bills"
        assert r.user_prob_pct == 65.0
        assert r.best_market_prob_pct == 50.0
        assert r.best_market_source == "draftkings"
        assert r.raw_edge == pytest.approx(0.15, abs=0.001)
        assert r.confidence_weight == 1.0
        assert r.kelly_fraction > 0
        assert r.kelly_stake > 0


class TestGetShortlist:
    def test_limits_to_n(self, db):
        slate = _setup_slate(db)
        for i in range(5):
            e = _add_event(db, slate.id, f"Team{i}", f"Opp{i}", confidence_tier="high")
            _add_estimate(db, e.id, 60.0 + i * 3)
            _add_line(db, e.id, "draftkings", 50.0, 2.0, outcome_name=f"Team{i}")

        shortlist = get_shortlist(db, slate.id, n=3)
        assert len(shortlist) == 3

    def test_returns_all_if_fewer_than_n(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id, confidence_tier="high")
        _add_estimate(db, e1.id, 65.0)
        _add_line(db, e1.id, "draftkings", 50.0, 2.0)

        shortlist = get_shortlist(db, slate.id, n=10)
        assert len(shortlist) == 1


class TestGetArbOpportunities:
    def test_aggregates_across_events(self, db):
        slate = _setup_slate(db)
        e1 = _add_event(db, slate.id, "Chiefs", "Bills")
        # Create arb: dk Chiefs at 45%, fd Bills at 48% → sum 93% < 97%
        store_lines(db, e1.id, [
            {
                "event_id": e1.id, "source": "draftkings", "market_key": "h2h",
                "outcome_name": "Chiefs",
                "implied_prob_pct": 45.0, "american_odds": None,
                "decimal_odds": 2.22, "fetched_at": datetime.now(tz=UTC),
                "raw_response": None,
            },
            {
                "event_id": e1.id, "source": "fanduel", "market_key": "h2h",
                "outcome_name": "Bills",
                "implied_prob_pct": 48.0, "american_odds": None,
                "decimal_odds": 2.08, "fetched_at": datetime.now(tz=UTC),
                "raw_response": None,
            },
        ])

        arbs = get_arb_opportunities(db, slate.id)
        assert len(arbs) >= 1
        assert arbs[0].arb_edge_pct > 0

    def test_empty_slate(self, db):
        slate = _setup_slate(db)
        assert get_arb_opportunities(db, slate.id) == []
