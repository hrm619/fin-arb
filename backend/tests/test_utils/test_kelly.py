"""Tests for Kelly criterion utility functions."""

import pytest

from backend.utils.kelly import kelly_fraction, fractional_kelly, kelly_stake


class TestKellyFraction:
    def test_positive_edge(self):
        # 60% true prob, decimal odds 2.0 (implied 50%)
        # edge = 0.10, p = 0.10 + 0.50 = 0.60, q = 0.40
        # kelly = (1*0.60 - 0.40) / 1 = 0.20
        result = kelly_fraction(0.10, 2.0)
        assert result == pytest.approx(0.20, abs=0.001)

    def test_no_edge(self):
        # Fair odds, no edge
        result = kelly_fraction(0.0, 2.0)
        assert result == 0.0

    def test_negative_edge_returns_zero(self):
        # Negative edge should clamp to 0
        result = kelly_fraction(-0.05, 2.0)
        assert result == 0.0

    def test_large_edge_long_odds(self):
        # 5% edge on +400 decimal (implied 25%)
        result = kelly_fraction(0.05, 4.0)
        assert result > 0

    def test_invalid_odds_raises(self):
        with pytest.raises(ValueError):
            kelly_fraction(0.10, 1.0)


class TestFractionalKelly:
    def test_quarter_kelly(self):
        full = kelly_fraction(0.10, 2.0)
        quarter = fractional_kelly(0.10, 2.0, 0.25)
        assert quarter == pytest.approx(full * 0.25, abs=0.0001)

    def test_half_kelly(self):
        full = kelly_fraction(0.10, 2.0)
        half = fractional_kelly(0.10, 2.0, 0.5)
        assert half == pytest.approx(full * 0.5, abs=0.0001)

    def test_default_fraction_is_quarter(self):
        full = kelly_fraction(0.10, 2.0)
        default = fractional_kelly(0.10, 2.0)
        assert default == pytest.approx(full * 0.25, abs=0.0001)


class TestKellyStake:
    def test_basic_stake(self):
        assert kelly_stake(1000.0, 0.05) == 50.0

    def test_zero_fraction(self):
        assert kelly_stake(1000.0, 0.0) == 0.0

    def test_zero_bankroll(self):
        assert kelly_stake(0.0, 0.10) == 0.0

    def test_negative_bankroll_raises(self):
        with pytest.raises(ValueError):
            kelly_stake(-100.0, 0.10)
