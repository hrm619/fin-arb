"""Pydantic schemas for Event request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    home_team: str
    away_team: str
    sport: str
    league: str
    external_event_id: str | None = None
    event_date: datetime
    market_type: str
    spread_value: float | None = None
    total_value: float | None = None
    confidence_tier: str | None = None


class EventBatchCreate(BaseModel):
    events: list["EventCreate"]


class EventUpdate(BaseModel):
    home_team: str | None = None
    away_team: str | None = None
    sport: str | None = None
    league: str | None = None
    external_event_id: str | None = None
    event_date: datetime | None = None
    market_type: str | None = None
    spread_value: float | None = None
    total_value: float | None = None
    confidence_tier: str | None = None
    status: str | None = None


class ConfidenceTierUpdate(BaseModel):
    confidence_tier: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slate_id: int
    home_team: str
    away_team: str
    sport: str
    league: str
    external_event_id: str | None
    event_date: datetime
    market_type: str
    spread_value: float | None
    total_value: float | None
    confidence_tier: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class EventResearchResponse(BaseModel):
    """Aggregated research data for a single event."""
    model_config = ConfigDict(from_attributes=True)

    event: EventResponse
    transcripts: list = []
    signals: list = []
    estimate: dict | None = None
    market_lines: list = []
