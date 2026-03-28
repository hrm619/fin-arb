"""Kalshi prediction market integration."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from backend.config import get_settings
from backend.utils.odds_converter import pct_to_american, pct_to_decimal


@dataclass
class KalshiMarket:
    id: str
    ticker: str
    title: str
    status: str
    yes_price: float  # 0-100 cents
    no_price: float


@dataclass
class KalshiOrderbook:
    market_id: str
    yes_bids: list[dict]
    yes_asks: list[dict]
    no_bids: list[dict]
    no_asks: list[dict]


async def search_markets(query: str) -> list[KalshiMarket]:
    """Search Kalshi markets by query string."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kalshi_base_url}/markets",
            params={"status": "open", "series_ticker": query},
            headers={"Authorization": f"Bearer {settings.kalshi_api_key}"},
        )
        resp.raise_for_status()
        return [_parse_market(m) for m in resp.json().get("markets", [])]


async def get_market(market_id: str) -> KalshiMarket:
    """Get a single Kalshi market by ID."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kalshi_base_url}/markets/{market_id}",
            headers={"Authorization": f"Bearer {settings.kalshi_api_key}"},
        )
        resp.raise_for_status()
        return _parse_market(resp.json().get("market", resp.json()))


async def get_orderbook(market_id: str) -> KalshiOrderbook:
    """Get the orderbook for a Kalshi market."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kalshi_base_url}/markets/{market_id}/orderbook",
            headers={"Authorization": f"Bearer {settings.kalshi_api_key}"},
        )
        resp.raise_for_status()
        data = resp.json().get("orderbook", resp.json())
        return KalshiOrderbook(
            market_id=market_id,
            yes_bids=data.get("yes", []),
            yes_asks=data.get("no", []),
            no_bids=data.get("no", []),
            no_asks=data.get("yes", []),
        )


def extract_implied_prob(orderbook: KalshiOrderbook) -> float:
    """Extract implied probability from the best yes bid price (cents → %)."""
    if orderbook.yes_bids:
        best_yes = max(orderbook.yes_bids, key=lambda b: b.get("price", 0))
        return float(best_yes.get("price", 50))
    return 50.0


def normalize_to_market_line(
    market: KalshiMarket, event_id: int, raw_response: dict | None = None
) -> dict:
    """Convert a KalshiMarket to a dict for creating a MarketLine model."""
    implied_prob = market.yes_price
    return {
        "event_id": event_id,
        "source": "kalshi",
        "market_key": market.ticker,
        "implied_prob_pct": implied_prob,
        "american_odds": pct_to_american(implied_prob) if 0 < implied_prob < 100 else None,
        "decimal_odds": pct_to_decimal(implied_prob) if 0 < implied_prob < 100 else None,
        "fetched_at": datetime.now(tz=UTC),
        "raw_response": raw_response,
    }


def _parse_market(data: dict) -> KalshiMarket:
    """Parse raw API market data into a KalshiMarket."""
    return KalshiMarket(
        id=data.get("id", data.get("ticker", "")),
        ticker=data.get("ticker", ""),
        title=data.get("title", ""),
        status=data.get("status", ""),
        yes_price=float(data.get("yes_price", data.get("last_price", 50))),
        no_price=float(data.get("no_price", 100 - data.get("last_price", 50))),
    )
