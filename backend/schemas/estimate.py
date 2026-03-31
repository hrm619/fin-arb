"""Pydantic schemas for UserEstimate request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EstimateCreate(BaseModel):
    probability_pct: float
    note: str | None = None
    suggested_estimate_id: int | None = None


class EstimateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    probability_pct: float
    american_odds: int | None
    decimal_odds: float | None
    note: str | None
    suggested_estimate_id: int | None = None
    override_delta: float | None = None
    locked_at: datetime
    created_at: datetime
