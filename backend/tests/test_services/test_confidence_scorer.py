"""Tests for composite confidence scoring."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from backend.schemas.structural_priors import ApplicableEdge
from backend.services.confidence_scorer import (
    compute_confidence,
    confidence_tier,
    line_confirmation,
    signal_coherence,
    structural_strength,
)


def _make_edge(quality_composite=2.5):
    return ApplicableEdge(
        edge_id="test__Q1", hypothesis_name="test", metric="m",
        bucket_label="Q1", edge_magnitude=0.05, quality_grade="HIGH",
        quality_composite=quality_composite, applies_to_team="Chiefs",
    )


def _make_signal(direction=1, relevance=0.8, user_flag=None):
    s = MagicMock()
    s.direction = direction
    s.relevance_score = relevance
    s.user_flag = user_flag
    return s


def _make_line(implied_prob, minutes_ago=0):
    l = MagicMock()
    l.implied_prob_pct = implied_prob
    l.fetched_at = datetime.now() - timedelta(minutes=minutes_ago)
    return l


class TestStructuralStrength:
    def test_single_high_edge(self):
        result = structural_strength([_make_edge(2.7)])
        assert result == round(2.7 / 3.0, 4)

    def test_multiple_edges(self):
        edges = [_make_edge(2.7), _make_edge(2.0)]
        result = structural_strength(edges)
        assert result == round(2.35 / 3.0, 4)

    def test_no_edges(self):
        assert structural_strength([]) == 0.0

    def test_capped_at_1(self):
        assert structural_strength([_make_edge(3.5)]) <= 1.0


class TestSignalCoherence:
    def test_all_same_direction(self):
        signals = [_make_signal(1, 0.8), _make_signal(1, 0.6)]
        assert signal_coherence(signals) == 1.0

    def test_mixed_directions(self):
        signals = [_make_signal(1, 0.8), _make_signal(-1, 0.8)]
        assert signal_coherence(signals) == 0.0

    def test_weighted_mixed(self):
        signals = [_make_signal(1, 0.9), _make_signal(-1, 0.3)]
        result = signal_coherence(signals)
        # |0.9 - 0.3| / (0.9 + 0.3) = 0.5
        assert result == 0.5

    def test_no_signals(self):
        assert signal_coherence([]) == 0.5

    def test_dismissed_excluded(self):
        signals = [_make_signal(1, 0.8, user_flag="dismissed")]
        assert signal_coherence(signals) == 0.5


class TestLineConfirmation:
    def test_no_movement(self):
        lines = [_make_line(55.0, 60), _make_line(55.0, 0)]
        assert line_confirmation(58.0, lines) == 0.0

    def test_movement_toward_estimate(self):
        lines = [_make_line(50.0, 60), _make_line(53.0, 0)]
        result = line_confirmation(55.0, lines)
        assert result > 0

    def test_movement_away_from_estimate(self):
        lines = [_make_line(55.0, 60), _make_line(52.0, 0)]
        result = line_confirmation(58.0, lines)
        assert result < 0

    def test_single_line(self):
        assert line_confirmation(55.0, [_make_line(55.0)]) == 0.0

    def test_capped_at_1(self):
        lines = [_make_line(40.0, 60), _make_line(60.0, 0)]
        result = line_confirmation(65.0, lines)
        assert result <= 1.0

    def test_floored_at_neg_half(self):
        lines = [_make_line(60.0, 60), _make_line(40.0, 0)]
        result = line_confirmation(65.0, lines)
        assert result >= -0.5


class TestConfidenceTier:
    def test_high(self):
        assert confidence_tier(0.70) == "high"
        assert confidence_tier(0.85) == "high"

    def test_medium(self):
        assert confidence_tier(0.40) == "medium"
        assert confidence_tier(0.69) == "medium"

    def test_low(self):
        assert confidence_tier(0.39) == "low"
        assert confidence_tier(0.0) == "low"


class TestComputeConfidence:
    def test_full_composite(self):
        edges = [_make_edge(2.5)]
        signals = [_make_signal(1, 0.8)]
        lines = [_make_line(50.0, 60), _make_line(52.0, 0)]

        result = compute_confidence(edges, signals, 55.0, lines)
        assert result.tier in ("high", "medium", "low")
        assert 0.0 <= result.composite_score <= 1.5
        assert result.weights_used["structural"] == 0.5
