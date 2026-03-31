"""Tests for the estimate composer."""

import pytest
from unittest.mock import MagicMock, patch

from backend.schemas.structural_priors import ApplicableEdge
from backend.services.composer import (
    QUALITY_WEIGHTS,
    _clamp,
    _quality_weight,
    compute_structural_adjustment,
)


def _make_edge(magnitude=0.05, grade="HIGH"):
    return ApplicableEdge(
        edge_id="test__Q1", hypothesis_name="test", metric="m",
        bucket_label="Q1", edge_magnitude=magnitude, quality_grade=grade,
        quality_composite=2.5, applies_to_team="Chiefs",
    )


class TestQualityWeight:
    def test_high(self):
        assert _quality_weight("HIGH") == 1.0

    def test_medium(self):
        assert _quality_weight("MEDIUM") == 0.6

    def test_low(self):
        assert _quality_weight("LOW") == 0.3

    def test_none_defaults(self):
        assert _quality_weight(None) == 0.3

    def test_unknown_defaults(self):
        assert _quality_weight("UNKNOWN") == 0.3


class TestClamp:
    def test_within_range(self):
        assert _clamp(55.0) == 55.0

    def test_below_min(self):
        assert _clamp(-5.0) == 1.0

    def test_above_max(self):
        assert _clamp(105.0) == 99.0

    def test_at_boundary(self):
        assert _clamp(1.0) == 1.0
        assert _clamp(99.0) == 99.0


class TestComputeStructuralAdjustment:
    @patch("backend.services.composer.get_settings")
    def test_single_high_edge(self, mock_settings):
        mock_settings.return_value.market_efficiency_discount = 0.5
        edges = [_make_edge(0.05, "HIGH")]
        # 0.05 * 1.0 * 0.5 * 100 = 2.5 pct points
        result = compute_structural_adjustment(edges)
        assert result == 2.5

    @patch("backend.services.composer.get_settings")
    def test_medium_edge(self, mock_settings):
        mock_settings.return_value.market_efficiency_discount = 0.5
        edges = [_make_edge(0.05, "MEDIUM")]
        # 0.05 * 0.6 * 0.5 * 100 = 1.5
        result = compute_structural_adjustment(edges)
        assert result == 1.5

    @patch("backend.services.composer.get_settings")
    def test_multiple_edges_sum(self, mock_settings):
        mock_settings.return_value.market_efficiency_discount = 0.5
        edges = [_make_edge(0.05, "HIGH"), _make_edge(-0.03, "LOW")]
        # 0.05 * 1.0 * 0.5 * 100 + (-0.03 * 0.3 * 0.5 * 100) = 2.5 - 0.45 = 2.05
        result = compute_structural_adjustment(edges)
        assert result == 2.05

    @patch("backend.services.composer.get_settings")
    def test_empty_edges(self, mock_settings):
        mock_settings.return_value.market_efficiency_discount = 0.5
        assert compute_structural_adjustment([]) == 0.0

    @patch("backend.services.composer.get_settings")
    def test_zero_discount(self, mock_settings):
        mock_settings.return_value.market_efficiency_discount = 0.0
        edges = [_make_edge(0.05, "HIGH")]
        # 0.05 * 1.0 * 1.0 * 100 = 5.0
        result = compute_structural_adjustment(edges)
        assert result == 5.0
