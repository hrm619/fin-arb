"""Tests for Polymarket integration (no live API calls)."""

import pytest

from backend.integrations.polymarket import (
    CLOBData,
    PolyMarket,
    _parse_market,
    extract_implied_prob,
    normalize_to_market_line,
)


SAMPLE_MARKET_DATA = {
    "condition_id": "0xabc123",
    "question": "Will the Chiefs win?",
    "outcome_prices": ["0.65", "0.35"],
}


class TestParseMarket:
    def test_parses_fields(self):
        m = _parse_market(SAMPLE_MARKET_DATA)
        assert m.condition_id == "0xabc123"
        assert m.question == "Will the Chiefs win?"
        assert m.outcome_prices == [0.65, 0.35]

    def test_camelcase_keys(self):
        data = {
            "conditionId": "0xdef",
            "question": "Test?",
            "outcomePrices": ["0.70", "0.30"],
        }
        m = _parse_market(data)
        assert m.condition_id == "0xdef"
        assert m.outcome_prices == [0.70, 0.30]

    def test_missing_prices(self):
        data = {"condition_id": "0x1", "question": "Q?"}
        m = _parse_market(data)
        assert m.outcome_prices == [0.5, 0.5]


class TestExtractImpliedProb:
    def test_mid_price_to_pct(self):
        clob = CLOBData(condition_id="x", best_bid=0.60, best_ask=0.70, mid_price=0.65)
        assert extract_implied_prob(clob) == 65.0

    def test_even_market(self):
        clob = CLOBData(condition_id="x", best_bid=0.50, best_ask=0.50, mid_price=0.50)
        assert extract_implied_prob(clob) == 50.0


class TestNormalizeToMarketLine:
    def test_produces_correct_dict(self):
        m = PolyMarket(condition_id="0xabc", question="Q?", outcome_prices=[0.65, 0.35])
        result = normalize_to_market_line(m, event_id=1)
        assert result["source"] == "polymarket"
        assert result["market_key"] == "0xabc"
        assert result["implied_prob_pct"] == 65.0
        assert result["american_odds"] == pytest.approx(-186, abs=1)
        assert result["decimal_odds"] == pytest.approx(1.5385, abs=0.01)
        assert result["event_id"] == 1

    def test_empty_prices(self):
        m = PolyMarket(condition_id="x", question="Q?", outcome_prices=[])
        result = normalize_to_market_line(m, event_id=1)
        assert result["implied_prob_pct"] == 50.0
