"""Business logic for sports and event browsing via Odds API."""

import logging
import time
from datetime import date, datetime, timezone

from backend.integrations import odds_api
from backend.integrations.odds_api import OddsEvent, Sport

logger = logging.getLogger(__name__)

_sports_cache: dict = {"data": [], "expires": 0.0}
_events_cache: dict[str, dict] = {}

SPORTS_TTL = 3600  # 1 hour
EVENTS_TTL = 300   # 5 minutes


async def list_sports() -> list[Sport]:
    """Return active sports, cached for 1 hour."""
    now = time.time()
    if _sports_cache["data"] and _sports_cache["expires"] > now:
        return _sports_cache["data"]

    sports = await odds_api.get_sports()
    active = [s for s in sports if s.active]
    _sports_cache["data"] = active
    _sports_cache["expires"] = now + SPORTS_TTL
    return active


async def list_events(
    sport_key: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[OddsEvent]:
    """Return upcoming events for a sport, filtered by date range."""
    now = time.time()
    cached = _events_cache.get(sport_key)
    if cached and cached["expires"] > now:
        events = cached["data"]
    else:
        events = await odds_api.get_events(sport_key)
        _events_cache[sport_key] = {"data": events, "expires": now + EVENTS_TTL}

    return _filter_by_date(events, date_from, date_to)


def _filter_by_date(
    events: list[OddsEvent],
    date_from: date | None,
    date_to: date | None,
) -> list[OddsEvent]:
    """Filter events to those within the given date range."""
    if not date_from and not date_to:
        return events
    filtered = []
    for e in events:
        event_date = e.commence_time.date()
        if date_from and event_date < date_from:
            continue
        if date_to and event_date > date_to:
            continue
        filtered.append(e)
    return filtered
