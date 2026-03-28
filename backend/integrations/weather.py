"""OpenWeatherMap integration for game-day weather forecasts."""

from dataclasses import dataclass
from datetime import datetime

import httpx

from backend.config import get_settings

BASE_URL = "https://api.openweathermap.org/data/2.5"

OUTDOOR_SPORTS = {"nfl", "mlb", "ncaaf", "soccer", "mls"}


@dataclass
class WeatherForecast:
    temp_f: float
    wind_mph: float
    humidity: int
    description: str
    precipitation_pct: float


async def get_forecast(
    lat: float, lon: float, event_datetime: datetime
) -> WeatherForecast:
    """Fetch weather forecast for a location and time."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": settings.weather_api_key,
                "units": "imperial",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return _find_closest_forecast(data, event_datetime)


def is_outdoor_sport(sport: str) -> bool:
    """Return True if the sport is typically played outdoors."""
    return sport.lower() in OUTDOOR_SPORTS


def format_weather_summary(forecast: WeatherForecast) -> str:
    """Format a weather forecast into a readable summary."""
    return (
        f"{forecast.description}, {forecast.temp_f:.0f}°F, "
        f"wind {forecast.wind_mph:.0f} mph, "
        f"humidity {forecast.humidity}%, "
        f"precip {forecast.precipitation_pct:.0f}%"
    )


def _find_closest_forecast(data: dict, target_dt: datetime) -> WeatherForecast:
    """Find the forecast entry closest to the target datetime."""
    forecasts = data.get("list", [])
    if not forecasts:
        return WeatherForecast(
            temp_f=0, wind_mph=0, humidity=0,
            description="unavailable", precipitation_pct=0,
        )

    best = min(
        forecasts,
        key=lambda f: abs(
            datetime.fromisoformat(f["dt_txt"]).timestamp() - target_dt.timestamp()
        ),
    )

    weather = best.get("weather", [{}])[0]
    main = best.get("main", {})
    wind = best.get("wind", {})

    return WeatherForecast(
        temp_f=main.get("temp", 0),
        wind_mph=wind.get("speed", 0),
        humidity=main.get("humidity", 0),
        description=weather.get("description", ""),
        precipitation_pct=best.get("pop", 0) * 100,
    )
