"""Tests for market anchor selection and vig removal."""

import pytest
from unittest.mock import MagicMock, patch

from backend.services.market_anchor import (
    _extract_vig_free_prob,
    _find_complement,
    _select_sharpest_line,
    get_market_anchor,
)


def _make_line(source="fanduel", outcome="Chiefs", implied_prob=55.0,
               decimal_odds=1.82, market_key="h2h"):
    line = MagicMock()
    line.source = source
    line.outcome_name = outcome
    line.implied_prob_pct = implied_prob
    line.decimal_odds = decimal_odds
    line.market_key = market_key
    return line


class TestSelectSharpestLine:
    @patch("backend.services.market_anchor.get_settings")
    def test_prefers_pinnacle(self, mock_settings):
        mock_settings.return_value.sharp_sources = "pinnacle,circa"
        lines = [
            _make_line("fanduel", "Chiefs", 55.0),
            _make_line("pinnacle", "Chiefs", 53.0),
            _make_line("draftkings", "Chiefs", 54.0),
        ]
        result = _select_sharpest_line(lines, "Chiefs")
        assert result.source == "pinnacle"

    @patch("backend.services.market_anchor.get_settings")
    def test_falls_back_to_lowest_prob(self, mock_settings):
        mock_settings.return_value.sharp_sources = "pinnacle,circa"
        lines = [
            _make_line("fanduel", "Chiefs", 55.0),
            _make_line("draftkings", "Chiefs", 52.0),
        ]
        result = _select_sharpest_line(lines, "Chiefs")
        assert result.implied_prob_pct == 52.0

    @patch("backend.services.market_anchor.get_settings")
    def test_no_matching_outcome(self, mock_settings):
        mock_settings.return_value.sharp_sources = "pinnacle"
        lines = [_make_line("fanduel", "Bills", 55.0)]
        result = _select_sharpest_line(lines, "Chiefs")
        assert result is None


class TestFindComplement:
    def test_finds_opposite_outcome(self):
        home = _make_line("pinnacle", "Chiefs", 55.0)
        away = _make_line("pinnacle", "Bills", 48.0)
        result = _find_complement(home, [home, away])
        assert result.outcome_name == "Bills"

    def test_no_complement_different_source(self):
        home = _make_line("pinnacle", "Chiefs", 55.0)
        away = _make_line("fanduel", "Bills", 48.0)
        result = _find_complement(home, [home, away])
        assert result is None


class TestExtractVigFreeProb:
    def test_removes_vig(self):
        home = _make_line("pinnacle", "Chiefs", 55.0)
        away = _make_line("pinnacle", "Bills", 48.0)
        result = _extract_vig_free_prob(home, [home, away])
        # 55 / (55+48) * 100 ≈ 53.40
        assert 53.0 < result < 54.0

    def test_no_complement_returns_raw(self):
        home = _make_line("pinnacle", "Chiefs", 55.0)
        result = _extract_vig_free_prob(home, [home])
        assert result == 55.0
