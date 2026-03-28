"""ESPN public API integration for injuries, team form, and head-to-head."""

from dataclasses import dataclass

import httpx

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

SPORT_MAP = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "mlb": "baseball/mlb",
    "nhl": "hockey/nhl",
    "ncaaf": "football/college-football",
    "ncaab": "basketball/mens-college-basketball",
}


@dataclass
class InjuryReport:
    player_name: str
    position: str
    status: str  # out, doubtful, questionable, probable
    detail: str


@dataclass
class GameResult:
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    winner: str


async def get_injuries(sport: str, team: str) -> list[InjuryReport]:
    """Fetch injury reports for a team."""
    sport_path = SPORT_MAP.get(sport)
    if not sport_path:
        return []

    team_id = await _find_team_id(sport_path, team)
    if not team_id:
        return []

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/{sport_path}/teams/{team_id}/injuries",
        )
        resp.raise_for_status()
        return [
            normalize_injury(item)
            for item in resp.json().get("items", [])
        ]


async def get_team_form(sport: str, team: str, last_n: int = 10) -> list[GameResult]:
    """Fetch recent game results for a team."""
    sport_path = SPORT_MAP.get(sport)
    if not sport_path:
        return []

    team_id = await _find_team_id(sport_path, team)
    if not team_id:
        return []

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/{sport_path}/teams/{team_id}/schedule",
        )
        resp.raise_for_status()
        events = resp.json().get("events", [])
        results = [_parse_game_result(e) for e in events if _is_completed(e)]
        return results[-last_n:]


async def get_head_to_head(
    sport: str, home_team: str, away_team: str
) -> list[GameResult]:
    """Fetch head-to-head results between two teams from recent form."""
    home_results = await get_team_form(sport, home_team, last_n=20)
    return [
        g for g in home_results
        if away_team.lower() in g.away_team.lower()
        or away_team.lower() in g.home_team.lower()
    ]


def normalize_injury(raw: dict) -> InjuryReport:
    """Parse raw ESPN injury data into an InjuryReport."""
    athlete = raw.get("athlete", {})
    return InjuryReport(
        player_name=athlete.get("displayName", "Unknown"),
        position=athlete.get("position", {}).get("abbreviation", ""),
        status=raw.get("status", "unknown"),
        detail=raw.get("longComment", raw.get("shortComment", "")),
    )


async def _find_team_id(sport_path: str, team_name: str) -> str | None:
    """Look up an ESPN team ID by name."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/{sport_path}/teams")
        resp.raise_for_status()
        for team_entry in resp.json().get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            team = team_entry.get("team", {})
            names = [
                team.get("displayName", "").lower(),
                team.get("shortDisplayName", "").lower(),
                team.get("abbreviation", "").lower(),
                team.get("name", "").lower(),
            ]
            if team_name.lower() in names:
                return team.get("id")
    return None


def _is_completed(event: dict) -> bool:
    """Check if an ESPN event is completed."""
    for comp in event.get("competitions", []):
        status = comp.get("status", {}).get("type", {})
        if status.get("completed", False):
            return True
    return False


def _parse_game_result(event: dict) -> GameResult:
    """Parse an ESPN event into a GameResult."""
    comp = event.get("competitions", [{}])[0]
    competitors = comp.get("competitors", [])
    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0] if competitors else {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})
    home_score = int(home.get("score", {}).get("value", home.get("score", 0)))
    away_score = int(away.get("score", {}).get("value", away.get("score", 0)))
    return GameResult(
        date=event.get("date", ""),
        home_team=home.get("team", {}).get("displayName", ""),
        away_team=away.get("team", {}).get("displayName", ""),
        home_score=home_score,
        away_score=away_score,
        winner=home.get("team", {}).get("displayName", "") if home_score > away_score else away.get("team", {}).get("displayName", ""),
    )
