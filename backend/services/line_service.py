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
    market_key = _market_type_to_odds_api(event.market_type)

    # Use stored event ID if available, fall back to fuzzy team match
    api_event_id = event.external_event_id
    if not api_event_id:
        api_event_id = await _find_odds_api_event(sport_key, event)
    if not api_event_id:
        logger.warning(
            "No Odds API event found for %s vs %s", event.home_team, event.away_team
        )
        return []

    odds_lines, raw = await odds_api.get_odds(
        sport_key=sport_key,
        event_id=api_event_id,
        markets=market_key,
    )
    return [
        odds_api.normalize_to_market_line(line, event.id, raw)
        for line in odds_lines
    ]


async def _find_odds_api_event(sport_key: str, event) -> str | None:
    """Find the Odds API event ID matching an event's teams."""
    api_events = await odds_api.get_events(sport_key)
    home = event.home_team.lower()
    away = event.away_team.lower()
    for api_event in api_events:
        api_home = api_event.home_team.lower()
        api_away = api_event.away_team.lower()
        if home in api_home or api_home in home:
            if away in api_away or api_away in away:
                return api_event.id
    return None


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


def get_best_line(
    db: Session, event_id: int, outcome_name: str | None = None
) -> MarketLine | None:
    """Return the line with the lowest implied probability (best value).

    If outcome_name is provided, only consider lines for that outcome.
    """
    lines = get_lines(db, event_id)
    if outcome_name:
        lines = [l for l in lines if l.outcome_name and
                 outcome_name.lower() in l.outcome_name.lower()]
    if not lines:
        return None
    return min(lines, key=lambda l: l.implied_prob_pct)


def detect_arb_opportunities(
    db: Session, event_id: int, threshold: float = 0.03
) -> list[ArbOpportunity]:
    """Find cross-market arb opportunities by pairing opposite outcomes."""
    lines = get_lines(db, event_id)
    opportunities: list[ArbOpportunity] = []

    for line_a, line_b in combinations(lines, 2):
        if line_a.source == line_b.source:
            continue
        # Only pair lines on different outcomes (e.g., Team A vs Team B)
        if not line_a.outcome_name or not line_b.outcome_name:
            continue
        if line_a.outcome_name == line_b.outcome_name:
            continue
        combined = line_a.implied_prob_pct + line_b.implied_prob_pct
        if is_arb_opportunity(line_a.implied_prob_pct, line_b.implied_prob_pct, threshold):
            opportunities.append(
                ArbOpportunity(
                    source_a=line_a.source,
                    source_b=line_b.source,
                    implied_prob_a=line_a.implied_prob_pct,
                    implied_prob_b=line_b.implied_prob_pct,
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
