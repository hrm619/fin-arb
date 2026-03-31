"""Team metrics provider — reads from factor-research's derived_metrics table."""

import logging
import sqlite3
from functools import lru_cache
from pathlib import Path

from backend.config import get_settings

logger = logging.getLogger(__name__)

# Map fin-arb team display names to factor-research canonical abbreviations
_TEAM_NAME_TO_ABBR: dict[str, str] = {
    "Cardinals": "ARI", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF",
    "Panthers": "CAR", "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE",
    "Cowboys": "DAL", "Broncos": "DEN", "Lions": "DET", "Packers": "GB",
    "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX", "Chiefs": "KC",
    "Raiders": "LVR", "Chargers": "LAC", "Rams": "LAR", "Dolphins": "MIA",
    "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG",
    "Jets": "NYJ", "Eagles": "PHI", "Steelers": "PIT", "49ers": "SF",
    "Seahawks": "SEA", "Buccaneers": "TB", "Titans": "TEN", "Commanders": "WAS",
    # Common alternative forms
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL", "Denver Broncos": "DEN",
    "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LVR", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN", "New England Patriots": "NE",
    "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
}


def normalize_team_name(name: str) -> str:
    """Map a fin-arb team name to a factor-research abbreviation."""
    if name in _TEAM_NAME_TO_ABBR:
        return _TEAM_NAME_TO_ABBR[name]
    # Already an abbreviation
    if len(name) <= 3 and name.isupper():
        return name
    # Try case-insensitive match on last word (e.g. "chiefs" -> "Chiefs")
    for display, abbr in _TEAM_NAME_TO_ABBR.items():
        if display.lower() == name.lower():
            return abbr
    logger.warning("Unknown team name: %s", name)
    return name


def get_team_metrics(
    team_abbr: str, season: int, week: int,
) -> dict[str, float | None]:
    """Query factor-research's derived_metrics for a team's entering-game metrics.

    Returns a dict mapping metric name to value. Empty dict if not found.
    """
    db_path = get_settings().factor_research_db_path
    if not Path(db_path).exists():
        logger.warning("Factor-research DB not found at %s", db_path)
        return {}

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM derived_metrics WHERE team_abbr = ? "
            "AND season = ? AND week = ?",
            (team_abbr, season, week),
        ).fetchone()
        conn.close()
    except sqlite3.OperationalError as e:
        logger.warning("Failed to query factor-research DB: %s", e)
        return {}

    if not row:
        return {}

    # Return all metric columns (skip team_abbr, game_id, season, week)
    skip = {"team_abbr", "game_id", "season", "week"}
    return {k: row[k] for k in row.keys() if k not in skip}


def get_latest_week(team_abbr: str, season: int) -> int | None:
    """Get the most recent week with metrics for a team in a season."""
    db_path = get_settings().factor_research_db_path
    if not Path(db_path).exists():
        return None

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT MAX(week) as max_week FROM derived_metrics "
            "WHERE team_abbr = ? AND season = ?",
            (team_abbr, season),
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None
