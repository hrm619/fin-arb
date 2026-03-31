"""Pydantic schemas for edge ranking responses."""

from pydantic import BaseModel, ConfigDict


class RankedEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: int
    home_team: str
    away_team: str
    sport: str
    market_type: str
    user_prob_pct: float
    best_market_prob_pct: float
    best_market_source: str
    raw_edge: float
    confidence_tier: str | None
    confidence_weight: float
    weighted_score: float
    kelly_fraction: float
    kelly_stake: float
    composite_confidence: float | None = None
