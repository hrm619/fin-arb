"""Tests for weather integration (no live API calls)."""

from datetime import datetime

from backend.integrations.weather import (
    WeatherForecast,
    _find_closest_forecast,
    format_weather_summary,
    is_outdoor_sport,
)


class TestIsOutdoorSport:
    def test_nfl(self):
        assert is_outdoor_sport("nfl") is True

    def test_mlb(self):
        assert is_outdoor_sport("mlb") is True

    def test_nba(self):
        assert is_outdoor_sport("nba") is False

    def test_nhl(self):
        assert is_outdoor_sport("nhl") is False

    def test_case_insensitive(self):
        assert is_outdoor_sport("NFL") is True


class TestFormatWeatherSummary:
    def test_formats(self):
        f = WeatherForecast(
            temp_f=45, wind_mph=15, humidity=60,
            description="light rain", precipitation_pct=80,
        )
        summary = format_weather_summary(f)
        assert "light rain" in summary
        assert "45°F" in summary
        assert "15 mph" in summary
        assert "60%" in summary
        assert "80%" in summary


class TestFindClosestForecast:
    def test_picks_closest(self):
        data = {
            "list": [
                {
                    "dt_txt": "2025-12-05 18:00:00",
                    "weather": [{"description": "clear"}],
                    "main": {"temp": 40, "humidity": 50},
                    "wind": {"speed": 10},
                    "pop": 0.1,
                },
                {
                    "dt_txt": "2025-12-05 21:00:00",
                    "weather": [{"description": "cloudy"}],
                    "main": {"temp": 35, "humidity": 60},
                    "wind": {"speed": 15},
                    "pop": 0.5,
                },
            ]
        }
        target = datetime(2025, 12, 5, 20, 0)
        result = _find_closest_forecast(data, target)
        assert result.description == "cloudy"
        assert result.temp_f == 35
        assert result.precipitation_pct == 50.0

    def test_empty_forecasts(self):
        result = _find_closest_forecast({"list": []}, datetime(2025, 12, 5))
        assert result.description == "unavailable"
