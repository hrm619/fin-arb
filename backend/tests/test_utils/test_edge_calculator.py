"""Tests for edge calculator utility functions."""

import pytest

from backend.utils.edge_calculator import (
    combined_implied_prob,
    is_arb_opportunity,
    is_meaningful_edge,
    raw_edge,
    vig_percentage,
)


class TestRawEdge:
    def test_positive_edge(self):
        # User thinks 60%, market says 50%
        assert raw_edge(60, 50) == pytest.approx(0.10, abs=0.001)

    def test_negative_edge(self):
        assert raw_edge(40, 50) == pytest.approx(-0.10, abs=0.001)

    def test_no_edge(self):
        assert raw_edge(50, 50) == 0.0


class TestIsMeaningfulEdge:
    def test_above_threshold(self):
        assert is_meaningful_edge(0.05) is True

    def test_below_threshold(self):
        assert is_meaningful_edge(0.02) is False

    def test_at_threshold(self):
        assert is_meaningful_edge(0.03) is False

    def test_custom_threshold(self):
        assert is_meaningful_edge(0.02, threshold=0.01) is True


class TestIsArbOpportunity:
    def test_arb_exists(self):
        # Two sides sum to 94% — 6% arb gap
        assert is_arb_opportunity(45, 49) is True

    def test_no_arb(self):
        # Two sides sum to 102% — no arb
        assert is_arb_opportunity(52, 50) is False

    def test_custom_threshold(self):
        # 45+45=90, threshold 5% → need < 95, so 90 qualifies
        assert is_arb_opportunity(45, 45, threshold=0.05) is True
        # 48+48=96, threshold 5% → need < 95, so 96 does not
        assert is_arb_opportunity(48, 48, threshold=0.05) is False

    def test_borderline(self):
        # Sum = 97, threshold 3% → need < 97, so not arb
        assert is_arb_opportunity(48.5, 48.5) is False


class TestCombinedImpliedProb:
    def test_two_sides(self):
        assert combined_implied_prob([52.5, 52.5]) == 105.0

    def test_three_sides(self):
        assert combined_implied_prob([35.0, 35.0, 35.0]) == 105.0

    def test_fair_market(self):
        assert combined_implied_prob([50.0, 50.0]) == 100.0


class TestVigPercentage:
    def test_normal_vig(self):
        assert vig_percentage(104.5) == 4.5

    def test_no_vig(self):
        assert vig_percentage(100.0) == 0.0

    def test_negative_vig(self):
        # Arb scenario
        assert vig_percentage(97.0) == -3.0
