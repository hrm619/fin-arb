"""Tests for Odds API integration (mocked HTTP)."""

import pytest

from backend.integrations.odds_api import (
    OddsLine,
    _parse_odds_response,
    normalize_to_market_line,
)


SAMPLE_API_RESPONSE = [
    {
        "id": "abc123",
        "sport_key": "americanfootball_nfl",
        "home_team": "Chiefs",
        "away_team": "Bills",
        "commence_time": "2025-12-05T01:00:00Z",
        "bookmakers": [
            {
                "key": "draftkings",
                "title": "DraftKings",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Chiefs", "price": -150},
                            {"name": "Bills", "price": 130},
                        ],
                    }
                ],
            },
            {
                "key": "fanduel",
                "title": "FanDuel",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Chiefs", "price": -145},
                            {"name": "Bills", "price": 125},
                        ],
                    }
                ],
            },
        ],
    }
]


class TestParseOddsResponse:
    def test_parses_all_lines(self):
        lines = _parse_odds_response(SAMPLE_API_RESPONSE)
        assert len(lines) == 4

    def test_line_fields(self):
        lines = _parse_odds_response(SAMPLE_API_RESPONSE)
        dk_chiefs = [l for l in lines if l.bookmaker == "draftkings" and l.outcome_name == "Chiefs"][0]
        assert dk_chiefs.price == -150
        assert dk_chiefs.market_key == "h2h"

    def test_empty_response(self):
        assert _parse_odds_response([]) == []

    def test_missing_bookmakers(self):
        data = [{"id": "x", "bookmakers": []}]
        assert _parse_odds_response(data) == []


class TestNormalizeToMarketLine:
    def test_produces_correct_dict(self):
        line = OddsLine(bookmaker="draftkings", market_key="h2h", outcome_name="Chiefs", price=-150)
        result = normalize_to_market_line(line, event_id=1)
        assert result["event_id"] == 1
        assert result["source"] == "draftkings"
        assert result["american_odds"] == -150
        assert result["implied_prob_pct"] == pytest.approx(60.0, abs=0.1)
        assert result["decimal_odds"] == pytest.approx(1.6667, abs=0.01)
        assert result["fetched_at"] is not None

    def test_positive_odds(self):
        line = OddsLine(bookmaker="fanduel", market_key="h2h", outcome_name="Bills", price=200)
        result = normalize_to_market_line(line, event_id=2)
        assert result["implied_prob_pct"] == pytest.approx(33.33, abs=0.1)
        assert result["decimal_odds"] == pytest.approx(3.0, abs=0.01)
