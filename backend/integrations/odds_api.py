"""The Odds API integration wrapper."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from backend.config import get_settings


@dataclass
class Sport:
    key: str
    group: str
    title: str
    active: bool


@dataclass
class OddsEvent:
    id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: datetime


@dataclass
class OddsLine:
    bookmaker: str
    market_key: str
    outcome_name: str
    price: int
    point: float | None = None


BASE_URL = "https://api.the-odds-api.com/v4"


async def get_sports() -> list[Sport]:
    """Fetch all available sports."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/sports",
            params={"apiKey": settings.odds_api_key},
        )
        resp.raise_for_status()
        return [
            Sport(
                key=s["key"],
                group=s["group"],
                title=s["title"],
                active=s["active"],
            )
            for s in resp.json()
        ]


async def get_events(sport_key: str) -> list[OddsEvent]:
    """Fetch upcoming events for a sport."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/sports/{sport_key}/events",
            params={"apiKey": settings.odds_api_key},
        )
        resp.raise_for_status()
        return [
            OddsEvent(
                id=e["id"],
                sport_key=e["sport_key"],
                home_team=e["home_team"],
                away_team=e["away_team"],
                commence_time=datetime.fromisoformat(e["commence_time"]),
            )
            for e in resp.json()
        ]


async def get_odds(
    sport_key: str,
    event_id: str,
    markets: str = "h2h",
    bookmakers: str | None = None,
) -> tuple[list[OddsLine], dict]:
    """Fetch odds for a specific event. Returns (parsed lines, raw response)."""
    settings = get_settings()
    params: dict = {
        "apiKey": settings.odds_api_key,
        "regions": "us",
        "markets": markets,
        "eventIds": event_id,
    }
    if bookmakers:
        params["bookmakers"] = bookmakers
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/sports/{sport_key}/odds",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        lines = _parse_odds_response(data)
        return lines, data


async def get_historical_odds(
    sport_key: str, event_id: str, date_iso: str
) -> tuple[list[OddsLine], dict]:
    """Fetch historical odds for an event at a given date."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/sports/{sport_key}/odds-history",
            params={
                "apiKey": settings.odds_api_key,
                "regions": "us",
                "markets": "h2h",
                "eventIds": event_id,
                "date": date_iso,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        raw_data = data.get("data", [])
        lines = _parse_odds_response(raw_data)
        return lines, data


def normalize_to_market_line(
    odds_line: OddsLine, event_id: int, raw_response: dict | None = None
) -> dict:
    """Convert an OddsLine to a dict suitable for creating a MarketLine model."""
    from backend.utils.odds_converter import american_to_decimal, american_to_pct

    implied_prob = american_to_pct(odds_line.price)
    decimal_odds = american_to_decimal(odds_line.price)
    return {
        "event_id": event_id,
        "source": odds_line.bookmaker,
        "market_key": odds_line.market_key,
        "implied_prob_pct": implied_prob,
        "american_odds": odds_line.price,
        "decimal_odds": decimal_odds,
        "fetched_at": datetime.now(tz=UTC),
        "raw_response": raw_response,
    }


def _parse_odds_response(data: list[dict]) -> list[OddsLine]:
    """Parse the nested odds API response into flat OddsLine objects."""
    lines: list[OddsLine] = []
    for event in data:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    lines.append(
                        OddsLine(
                            bookmaker=bookmaker["key"],
                            market_key=market["key"],
                            outcome_name=outcome["name"],
                            price=outcome["price"],
                            point=outcome.get("point"),
                        )
                    )
    return lines
