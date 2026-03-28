"""Sports browsing API routes (Odds API proxy)."""

from datetime import date

from fastapi import APIRouter, Query

from backend.schemas.sports import OddsEventResponse, SportResponse
from backend.services import sports_service

router = APIRouter(prefix="/api/v1", tags=["sports"])


@router.get("/sports", response_model=list[SportResponse])
async def list_sports():
    """List all active sports from The Odds API."""
    return await sports_service.list_sports()


@router.get(
    "/sports/{sport_key}/events",
    response_model=list[OddsEventResponse],
)
async def list_sport_events(
    sport_key: str,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    """List upcoming events for a sport, optionally filtered by date range."""
    return await sports_service.list_events(sport_key, date_from, date_to)
