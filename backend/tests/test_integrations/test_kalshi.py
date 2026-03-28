"""Tests for Kalshi integration (no live API calls)."""

import pytest

from backend.integrations.kalshi import (
    KalshiMarket,
    KalshiOrderbook,
    _parse_market,
    extract_implied_prob,
    normalize_to_market_line,
)


SAMPLE_MARKET_DATA = {
    "id": "market-123",
    "ticker": "NFL-CHIEFS-WIN",
    "title": "Will the Chiefs win?",
    "status": "open",
    "yes_price": 65,
    "no_price": 35,
}


class TestParseMarket:
    def test_parses_fields(self):
        m = _parse_market(SAMPLE_MARKET_DATA)
        assert m.ticker == "NFL-CHIEFS-WIN"
        assert m.yes_price == 65
        assert m.no_price == 35

    def test_fallback_on_last_price(self):
        data = {"ticker": "X", "title": "T", "status": "open", "last_price": 70}
        m = _parse_market(data)
        assert m.yes_price == 70
        assert m.no_price == 30


class TestExtractImpliedProb:
    def test_uses_best_yes_bid(self):
        ob = KalshiOrderbook(
            market_id="m1",
            yes_bids=[{"price": 60}, {"price": 55}],
            yes_asks=[],
            no_bids=[],
            no_asks=[],
        )
        assert extract_implied_prob(ob) == 60.0

    def test_default_when_no_bids(self):
        ob = KalshiOrderbook(
            market_id="m1", yes_bids=[], yes_asks=[], no_bids=[], no_asks=[]
        )
        assert extract_implied_prob(ob) == 50.0


class TestNormalizeToMarketLine:
    def test_produces_correct_dict(self):
        m = KalshiMarket(
            id="m1", ticker="NFL-X", title="Test", status="open",
            yes_price=65, no_price=35,
        )
        result = normalize_to_market_line(m, event_id=1)
        assert result["source"] == "kalshi"
        assert result["market_key"] == "NFL-X"
        assert result["implied_prob_pct"] == 65
        assert result["american_odds"] == pytest.approx(-186, abs=1)
        assert result["decimal_odds"] == pytest.approx(1.5385, abs=0.01)
        assert result["event_id"] == 1

    def test_boundary_price_no_odds(self):
        m = KalshiMarket(
            id="m1", ticker="X", title="T", status="open",
            yes_price=0, no_price=100,
        )
        result = normalize_to_market_line(m, event_id=1)
        assert result["american_odds"] is None
        assert result["decimal_odds"] is None
