"""Tests for structural priors edge matching."""

import pytest
from unittest.mock import patch

from backend.services.structural_priors import (
    _matches_bucket,
    get_applicable_edges,
    load_edge_registry,
)
from backend.services.stats_provider import normalize_team_name


SAMPLE_REGISTRY = {
    "contract_version": "1.0.0",
    "producer": "factor-research",
    "domain": "nfl",
    "edges": [
        {
            "edge_id": "defensive_test__Q1",
            "hypothesis_name": "defensive_test",
            "metric": "points_allowed_per_game_std",
            "bucket_label": "Q1",
            "outcome_type": "ats",
            "lookback": "season_to_date",
            "measurement": {
                "cover_rate": 0.56,
                "edge_magnitude": 0.06,
                "n": 128,
                "p_value": 0.05,
            },
            "quality": {"grade": "MEDIUM", "composite_score": 2.1},
            "applicability": {
                "metric_direction": "higher_is_better",
                "applies_to": "either",
                "classification_type": "quartile",
            },
        },
        {
            "edge_id": "defensive_test__Q4",
            "hypothesis_name": "defensive_test",
            "metric": "points_allowed_per_game_std",
            "bucket_label": "Q4",
            "outcome_type": "ats",
            "lookback": "season_to_date",
            "measurement": {
                "cover_rate": 0.44,
                "edge_magnitude": -0.06,
                "n": 128,
                "p_value": 0.05,
            },
            "quality": {"grade": "MEDIUM", "composite_score": 2.1},
            "applicability": {
                "metric_direction": "lower_is_better",
                "applies_to": "either",
                "classification_type": "quartile",
            },
        },
    ],
}

SAMPLE_METRICS = {
    "points_allowed_per_game_std": 18.5,
    "yards_per_game_std": 350.0,
}


class TestNormalizeTeamName:
    def test_full_name(self):
        assert normalize_team_name("Chiefs") == "KC"

    def test_city_and_name(self):
        assert normalize_team_name("Kansas City Chiefs") == "KC"

    def test_already_abbr(self):
        assert normalize_team_name("KC") == "KC"

    def test_case_insensitive(self):
        assert normalize_team_name("chiefs") == "KC"


class TestMatchesBucket:
    def test_quartile_q1_higher(self):
        result = _matches_bucket(18.5, "Q1", "quartile", "higher_is_better")
        assert result == 18.5

    def test_quartile_q4_lower(self):
        result = _matches_bucket(28.0, "Q4", "quartile", "lower_is_better")
        assert result == 28.0

    def test_quartile_q1_wrong_direction(self):
        result = _matches_bucket(18.5, "Q1", "quartile", "lower_is_better")
        assert result is None

    def test_binary_above(self):
        result = _matches_bucket(25.0, "above", "binary", "higher_is_better")
        assert result == 25.0

    def test_binary_below(self):
        result = _matches_bucket(15.0, "below", "binary", "lower_is_better")
        assert result == 15.0


class TestGetApplicableEdges:
    @patch("backend.services.structural_priors.get_team_metrics")
    @patch("backend.services.structural_priors.get_latest_week")
    def test_finds_matching_edges(self, mock_week, mock_metrics):
        mock_week.return_value = 10
        mock_metrics.return_value = SAMPLE_METRICS

        edges = get_applicable_edges(
            "Chiefs", "Bills", season=2024, week=10,
            registry=SAMPLE_REGISTRY,
        )
        # Both teams have metrics, Q1 (higher_is_better) should match
        assert len(edges) > 0
        assert all(e.metric == "points_allowed_per_game_std" for e in edges)

    @patch("backend.services.structural_priors.get_team_metrics")
    @patch("backend.services.structural_priors.get_latest_week")
    def test_no_metrics_returns_empty(self, mock_week, mock_metrics):
        mock_week.return_value = 10
        mock_metrics.return_value = {}

        edges = get_applicable_edges(
            "Chiefs", "Bills", season=2024, week=10,
            registry=SAMPLE_REGISTRY,
        )
        assert edges == []

    def test_empty_registry(self):
        edges = get_applicable_edges(
            "Chiefs", "Bills", season=2024, week=10,
            registry={"edges": []},
        )
        assert edges == []


class TestLoadEdgeRegistry:
    def test_missing_file_returns_empty(self, tmp_path):
        result = load_edge_registry(str(tmp_path / "nonexistent.json"))
        assert result == {"edges": []}

    def test_loads_valid_file(self, tmp_path):
        import json
        p = tmp_path / "edges.json"
        p.write_text(json.dumps(SAMPLE_REGISTRY))
        result = load_edge_registry(str(p))
        assert len(result["edges"]) == 2
