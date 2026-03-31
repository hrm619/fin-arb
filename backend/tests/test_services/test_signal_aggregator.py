"""Tests for signal aggregation with type-specific caps."""

import pytest
from unittest.mock import MagicMock

from backend.services.signal_aggregator import (
    SIGNAL_CAPS,
    aggregate_signals,
    compute_signal_adjustment,
)


def _make_signal(signal_type="injury", direction=1, relevance=0.8,
                 user_flag=None, signal_id=1):
    s = MagicMock()
    s.id = signal_id
    s.signal_type = signal_type
    s.direction = direction
    s.relevance_score = relevance
    s.user_flag = user_flag
    return s


class TestComputeSignalAdjustment:
    def test_injury_positive(self):
        assert compute_signal_adjustment(1, 0.8, "injury") == 4.0

    def test_injury_negative(self):
        assert compute_signal_adjustment(-1, 0.8, "injury") == -4.0

    def test_sentiment_capped(self):
        assert compute_signal_adjustment(1, 1.0, "sentiment") == 1.0

    def test_scheme(self):
        assert compute_signal_adjustment(1, 0.5, "scheme") == 1.0

    def test_unknown_type_defaults_to_1(self):
        assert compute_signal_adjustment(1, 1.0, "unknown") == 1.0


class TestAggregateSignals:
    def test_single_signal(self):
        signals = [_make_signal(direction=1, relevance=0.8)]
        result = aggregate_signals(signals)
        assert result.signal_count == 1
        assert result.total_adjustment == 4.0

    def test_mixed_directions(self):
        signals = [
            _make_signal("injury", direction=1, relevance=0.8, signal_id=1),
            _make_signal("scheme", direction=-1, relevance=0.5, signal_id=2),
        ]
        result = aggregate_signals(signals)
        assert result.signal_count == 2
        assert result.total_adjustment == 3.0  # 4.0 + (-1.0)

    def test_dismissed_excluded(self):
        signals = [_make_signal(user_flag="dismissed")]
        result = aggregate_signals(signals)
        assert result.signal_count == 0
        assert result.total_adjustment == 0.0

    def test_no_direction_excluded(self):
        signals = [_make_signal(direction=None)]
        result = aggregate_signals(signals)
        assert result.signal_count == 0

    def test_no_relevance_excluded(self):
        signals = [_make_signal(relevance=None)]
        result = aggregate_signals(signals)
        assert result.signal_count == 0

    def test_empty_list(self):
        result = aggregate_signals([])
        assert result.signal_count == 0
        assert result.total_adjustment == 0.0

    def test_all_caps_present(self):
        for signal_type, cap in SIGNAL_CAPS.items():
            adj = compute_signal_adjustment(1, 1.0, signal_type)
            assert adj == cap
