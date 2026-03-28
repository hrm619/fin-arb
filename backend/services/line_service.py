"""Business logic for market line operations."""

import logging
from datetime import datetime
from itertools import combinations

from sqlalchemy.orm import Session

from backend.integrations import kalshi, odds_api, polymarket
from backend.models.market_line import MarketLine
from backend.schemas.market_line import ArbOpportunity
from backend.services.event_service import get_event
from backend.utils.edge_calculator import is_arb_opportunity

logger = logging.getLogger(__name__)


async def fetch_lines(db: Session, event_id: int) -> list[MarketLine]:
    """Orchestrate line fetching from all available sources."""
    event = get_event(db, event_id)
    all_line_dicts: list[dict] = []

    for fetch_fn, name in [
        (fetch_odds_api_lines, "Odds API"),
        (fetch_kalshi_lines, "Kalshi"),
        (fetch_polymarket_lines, "Polymarket"),
    ]:
        try:
            lines = await fetch_fn(event)
            all_line_dicts.extend(lines)
        except Exception:
            logger.exception("Failed to fetch %s lines for event %s", name, event_id)

    return store_lines(db, event_id, all_line_dicts)


async def fetch_odds_api_lines(event) -> list[dict]:
    """Fetch lines from The Odds API for a given event."""
    sport_key = event.sport
    odds_lines, raw = await odds_api.get_odds(
        sport_key=sport_key,
        event_id="",  # fetch all for sport, filter client-side
        markets=_market_type_to_odds_api(event.market_type),
    )
    return [
        odds_api.normalize_to_market_line(line, event.id, raw)
        for line in odds_lines
    ]


async def fetch_kalshi_lines(event) -> list[dict]:
    """Fetch lines from Kalshi for a given event."""
    query = f"{event.home_team} {event.away_team}"
    markets = await kalshi.search_markets(query)
    return [kalshi.normalize_to_market_line(m, event.id) for m in markets]


async def fetch_polymarket_lines(event) -> list[dict]:
    """Fetch lines from Polymarket for a given event."""
    query = f"{event.home_team} {event.away_team}"
    markets = await polymarket.search_markets(query)
    return [polymarket.normalize_to_market_line(m, event.id) for m in markets]


def store_lines(db: Session, event_id: int, line_dicts: list[dict]) -> list[MarketLine]:
    """Persist a batch of line dicts as MarketLine rows."""
    models = []
    for ld in line_dicts:
        ml = MarketLine(**ld)
        db.add(ml)
        models.append(ml)
    db.commit()
    for m in models:
        db.refresh(m)
    return models


def get_lines(db: Session, event_id: int) -> list[MarketLine]:
    """Return all stored lines for an event."""
    return list(
        db.query(MarketLine)
        .filter(MarketLine.event_id == event_id)
        .order_by(MarketLine.fetched_at.desc())
        .all()
    )


def get_best_line(db: Session, event_id: int) -> MarketLine | None:
    """Return the line with the lowest implied probability (best value)."""
    lines = get_lines(db, event_id)
    if not lines:
        return None
    return min(lines, key=lambda l: l.implied_prob_pct)


def detect_arb_opportunities(
    db: Session, event_id: int, threshold: float = 0.03
) -> list[ArbOpportunity]:
    """Find cross-market arb opportunities for an event."""
    lines = get_lines(db, event_id)
    opportunities: list[ArbOpportunity] = []

    for line_a, line_b in combinations(lines, 2):
        if line_a.source == line_b.source:
            continue
        # Check both directions: a vs complement(b), b vs complement(a)
        for la, lb in [(line_a, line_b), (line_b, line_a)]:
            complement = 100 - lb.implied_prob_pct
            if is_arb_opportunity(la.implied_prob_pct, complement, threshold):
                combined = la.implied_prob_pct + complement
                opportunities.append(
                    ArbOpportunity(
                        source_a=la.source,
                        source_b=lb.source,
                        implied_prob_a=la.implied_prob_pct,
                        implied_prob_b=complement,
                        combined_prob=combined,
                        arb_edge_pct=round(100 - combined, 4),
                    )
                )

    return sorted(opportunities, key=lambda a: a.arb_edge_pct, reverse=True)


def _market_type_to_odds_api(market_type: str) -> str:
    """Map internal market type to Odds API market key."""
    mapping = {
        "moneyline": "h2h",
        "spread": "spreads",
        "over_under": "totals",
    }
    return mapping.get(market_type, "h2h")
