"""Tests for ESPN integration (no live API calls)."""

from backend.integrations.espn import (
    GameResult,
    InjuryReport,
    _is_completed,
    _parse_game_result,
    normalize_injury,
)


SAMPLE_INJURY = {
    "athlete": {
        "displayName": "Patrick Mahomes",
        "position": {"abbreviation": "QB"},
    },
    "status": "questionable",
    "longComment": "Ankle - questionable for Sunday",
}

SAMPLE_EVENT = {
    "date": "2025-12-05T01:00Z",
    "competitions": [
        {
            "status": {"type": {"completed": True}},
            "competitors": [
                {
                    "homeAway": "home",
                    "team": {"displayName": "Kansas City Chiefs"},
                    "score": {"value": 24},
                },
                {
                    "homeAway": "away",
                    "team": {"displayName": "Buffalo Bills"},
                    "score": {"value": 17},
                },
            ],
        }
    ],
}


class TestNormalizeInjury:
    def test_parses_fields(self):
        report = normalize_injury(SAMPLE_INJURY)
        assert report.player_name == "Patrick Mahomes"
        assert report.position == "QB"
        assert report.status == "questionable"
        assert "Ankle" in report.detail

    def test_missing_fields(self):
        report = normalize_injury({})
        assert report.player_name == "Unknown"
        assert report.status == "unknown"


class TestIsCompleted:
    def test_completed_event(self):
        assert _is_completed(SAMPLE_EVENT) is True

    def test_incomplete_event(self):
        event = {"competitions": [{"status": {"type": {"completed": False}}}]}
        assert _is_completed(event) is False

    def test_missing_status(self):
        assert _is_completed({}) is False


class TestParseGameResult:
    def test_parses_completed_game(self):
        result = _parse_game_result(SAMPLE_EVENT)
        assert result.home_team == "Kansas City Chiefs"
        assert result.away_team == "Buffalo Bills"
        assert result.home_score == 24
        assert result.away_score == 17
        assert result.winner == "Kansas City Chiefs"

    def test_away_team_wins(self):
        event = {
            "date": "2025-12-05",
            "competitions": [{
                "competitors": [
                    {"homeAway": "home", "team": {"displayName": "A"}, "score": {"value": 10}},
                    {"homeAway": "away", "team": {"displayName": "B"}, "score": {"value": 20}},
                ],
            }],
        }
        result = _parse_game_result(event)
        assert result.winner == "B"
