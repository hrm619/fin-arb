"""Pydantic schemas for sports browsing endpoints."""

from datetime import datetime

from pydantic import BaseModel


class SportResponse(BaseModel):
    key: str
    group: str
    title: str
    active: bool


class OddsEventResponse(BaseModel):
    id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: datetime
