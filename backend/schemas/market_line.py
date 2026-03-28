"""Pydantic schemas for MarketLine request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MarketLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    source: str
    outcome_name: str | None
    market_key: str | None
    implied_prob_pct: float
    american_odds: int | None
    decimal_odds: float | None
    fetched_at: datetime


class ArbOpportunity(BaseModel):
    source_a: str
    source_b: str
    implied_prob_a: float
    implied_prob_b: float
    combined_prob: float
    arb_edge_pct: float
