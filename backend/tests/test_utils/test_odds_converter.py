"""Tests for odds_converter utility functions."""

import pytest

from backend.utils.odds_converter import (
    american_to_decimal,
    american_to_pct,
    decimal_to_american,
    decimal_to_pct,
    pct_to_american,
    pct_to_decimal,
    remove_vig,
)


# --- pct_to_american ---

class TestPctToAmerican:
    def test_favorite(self):
        assert pct_to_american(70) == -233

    def test_underdog(self):
        assert pct_to_american(30) == 233

    def test_even(self):
        assert pct_to_american(50) == -100

    def test_heavy_favorite(self):
        assert pct_to_american(90) == -900

    def test_big_underdog(self):
        assert pct_to_american(10) == 900

    def test_boundary_low_raises(self):
        with pytest.raises(ValueError):
            pct_to_american(0)

    def test_boundary_high_raises(self):
        with pytest.raises(ValueError):
            pct_to_american(100)


# --- pct_to_decimal ---

class TestPctToDecimal:
    def test_even(self):
        assert pct_to_decimal(50) == 2.0

    def test_favorite(self):
        assert pct_to_decimal(80) == 1.25

    def test_underdog(self):
        assert pct_to_decimal(25) == 4.0

    def test_boundary_raises(self):
        with pytest.raises(ValueError):
            pct_to_decimal(0)


# --- american_to_pct ---

class TestAmericanToPct:
    def test_negative_odds(self):
        assert american_to_pct(-200) == pytest.approx(66.6667, abs=0.001)

    def test_positive_odds(self):
        assert american_to_pct(200) == pytest.approx(33.3333, abs=0.001)

    def test_minus_100(self):
        assert american_to_pct(-100) == 50.0

    def test_plus_100(self):
        assert american_to_pct(100) == 50.0

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            american_to_pct(0)


# --- american_to_decimal ---

class TestAmericanToDecimal:
    def test_negative_odds(self):
        assert american_to_decimal(-200) == 1.5

    def test_positive_odds(self):
        assert american_to_decimal(200) == 3.0

    def test_minus_100(self):
        assert american_to_decimal(-100) == 2.0

    def test_plus_100(self):
        assert american_to_decimal(100) == 2.0

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            american_to_decimal(0)


# --- decimal_to_pct ---

class TestDecimalToPct:
    def test_even(self):
        assert decimal_to_pct(2.0) == 50.0

    def test_favorite(self):
        assert decimal_to_pct(1.25) == 80.0

    def test_underdog(self):
        assert decimal_to_pct(4.0) == 25.0

    def test_boundary_raises(self):
        with pytest.raises(ValueError):
            decimal_to_pct(1.0)


# --- decimal_to_american ---

class TestDecimalToAmerican:
    def test_plus_odds(self):
        assert decimal_to_american(3.0) == 200

    def test_minus_odds(self):
        assert decimal_to_american(1.5) == -200

    def test_even(self):
        assert decimal_to_american(2.0) == 100

    def test_boundary_raises(self):
        with pytest.raises(ValueError):
            decimal_to_american(0.5)


# --- remove_vig ---

class TestRemoveVig:
    def test_balanced_market(self):
        fair_a, fair_b = remove_vig(52.5, 52.5)
        assert fair_a == pytest.approx(50.0, abs=0.01)
        assert fair_b == pytest.approx(50.0, abs=0.01)

    def test_skewed_market(self):
        fair_a, fair_b = remove_vig(60, 50)
        assert fair_a + fair_b == pytest.approx(100.0, abs=0.01)
        assert fair_a > fair_b

    def test_zero_sum_raises(self):
        with pytest.raises(ValueError):
            remove_vig(0, 0)


# --- Round-trip consistency ---

class TestRoundTrips:
    @pytest.mark.parametrize("pct", [10, 25, 33, 50, 67, 75, 90])
    def test_pct_american_roundtrip(self, pct):
        american = pct_to_american(pct)
        recovered = american_to_pct(american)
        assert recovered == pytest.approx(pct, abs=1.0)

    @pytest.mark.parametrize("pct", [10, 25, 33, 50, 67, 75, 90])
    def test_pct_decimal_roundtrip(self, pct):
        decimal = pct_to_decimal(pct)
        recovered = decimal_to_pct(decimal)
        assert recovered == pytest.approx(pct, abs=0.1)

    @pytest.mark.parametrize("american", [-500, -200, 100, 200, 500])
    def test_american_decimal_roundtrip(self, american):
        decimal = american_to_decimal(american)
        recovered = decimal_to_american(decimal)
        assert recovered == pytest.approx(american, abs=1)

    def test_even_money_boundary(self):
        # -100 and +100 both map to decimal 2.0; roundtrip yields +100
        assert american_to_decimal(-100) == 2.0
        assert american_to_decimal(100) == 2.0
        assert decimal_to_american(2.0) == 100
