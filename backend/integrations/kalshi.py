"""Kalshi prediction market integration with RSA-PSS authentication."""

import base64
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from backend.config import get_settings
from backend.utils.odds_converter import pct_to_american, pct_to_decimal

logger = logging.getLogger(__name__)


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


def _load_private_key():
    """Load the RSA private key from the configured path."""
    settings = get_settings()
    key_path = Path(settings.kalshi_rsa_key_path)
    if not key_path.exists():
        raise ValueError(f"Kalshi RSA key not found at {key_path}")
    return serialization.load_pem_private_key(
        key_path.read_bytes(), password=None, backend=default_backend()
    )


def _sign_request(private_key, timestamp_ms: str, method: str, path: str) -> str:
    """Create RSA-PSS signature for Kalshi API authentication."""
    path_without_query = path.split("?")[0]
    message = f"{timestamp_ms}{method}{path_without_query}".encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _auth_headers(method: str, path: str) -> dict[str, str]:
    """Build authenticated headers for a Kalshi API request."""
    settings = get_settings()
    private_key = _load_private_key()
    timestamp_ms = str(int(datetime.now(tz=UTC).timestamp() * 1000))
    signature = _sign_request(private_key, timestamp_ms, method, path)
    return {
        "KALSHI-ACCESS-KEY": settings.kalshi_api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
        "Content-Type": "application/json",
    }


async def search_markets(query: str) -> list[KalshiMarket]:
    """Search Kalshi events by query, then return their markets."""
    settings = get_settings()
    path = "/trade-api/v2/events"
    params = {"status": "open", "limit": 20}
    headers = _auth_headers("GET", path)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kalshi_base_url}/events",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        events = resp.json().get("events", [])

    # Filter events whose title contains the query terms
    query_lower = query.lower()
    terms = query_lower.split()
    matching: list[KalshiMarket] = []
    for event in events:
        title = event.get("title", "").lower()
        if any(term in title for term in terms):
            for market in event.get("markets", []):
                matching.append(_parse_market(market))
    return matching


async def get_market(market_id: str) -> KalshiMarket:
    """Get a single Kalshi market by ID."""
    settings = get_settings()
    path = f"/trade-api/v2/markets/{market_id}"
    headers = _auth_headers("GET", path)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kalshi_base_url}/markets/{market_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return _parse_market(resp.json().get("market", resp.json()))


async def get_orderbook(market_id: str) -> KalshiOrderbook:
    """Get the orderbook for a Kalshi market."""
    settings = get_settings()
    path = f"/trade-api/v2/markets/{market_id}/orderbook"
    headers = _auth_headers("GET", path)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kalshi_base_url}/markets/{market_id}/orderbook",
            headers=headers,
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
        "outcome_name": market.title,
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
