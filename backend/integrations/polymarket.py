"""Polymarket prediction market integration."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from backend.config import get_settings
from backend.utils.odds_converter import pct_to_american, pct_to_decimal


@dataclass
class PolyMarket:
    condition_id: str
    question: str
    outcome_prices: list[float]  # [yes_price, no_price] as 0-1


@dataclass
class CLOBData:
    condition_id: str
    best_bid: float
    best_ask: float
    mid_price: float


async def search_markets(query: str) -> list[PolyMarket]:
    """Search Polymarket markets by query."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.polymarket_base_url}/markets",
            params={"query": query},
        )
        resp.raise_for_status()
        return [_parse_market(m) for m in resp.json() if isinstance(m, dict)]


async def get_market(condition_id: str) -> PolyMarket:
    """Get a single Polymarket market."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.polymarket_base_url}/markets/{condition_id}",
        )
        resp.raise_for_status()
        return _parse_market(resp.json())


async def get_clob_data(condition_id: str) -> CLOBData:
    """Get CLOB (order book) data for a Polymarket market."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.polymarket_base_url}/book",
            params={"token_id": condition_id},
        )
        resp.raise_for_status()
        data = resp.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        best_bid = float(bids[0]["price"]) if bids else 0.5
        best_ask = float(asks[0]["price"]) if asks else 0.5
        return CLOBData(
            condition_id=condition_id,
            best_bid=best_bid,
            best_ask=best_ask,
            mid_price=(best_bid + best_ask) / 2,
        )


def extract_implied_prob(clob_data: CLOBData) -> float:
    """Extract implied probability from CLOB mid-price (0-1 → 0-100%)."""
    return round(clob_data.mid_price * 100, 4)


def normalize_to_market_line(
    market: PolyMarket, event_id: int, raw_response: dict | None = None
) -> dict:
    """Convert a PolyMarket to a dict for creating a MarketLine model."""
    implied_prob = market.outcome_prices[0] * 100 if market.outcome_prices else 50.0
    return {
        "event_id": event_id,
        "source": "polymarket",
        "market_key": market.condition_id,
        "implied_prob_pct": implied_prob,
        "american_odds": pct_to_american(implied_prob) if 0 < implied_prob < 100 else None,
        "decimal_odds": pct_to_decimal(implied_prob) if 0 < implied_prob < 100 else None,
        "fetched_at": datetime.now(tz=UTC),
        "raw_response": raw_response,
    }


def _parse_market(data: dict) -> PolyMarket:
    """Parse raw API data into a PolyMarket."""
    prices = data.get("outcome_prices", data.get("outcomePrices", []))
    parsed_prices = [float(p) for p in prices] if prices else [0.5, 0.5]
    return PolyMarket(
        condition_id=data.get("condition_id", data.get("conditionId", "")),
        question=data.get("question", ""),
        outcome_prices=parsed_prices,
    )
