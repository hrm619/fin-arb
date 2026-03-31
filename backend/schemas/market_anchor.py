"""Pydantic schemas for market anchor responses."""

from pydantic import BaseModel


class MarketAnchor(BaseModel):
    source: str
    raw_implied_prob_pct: float
    vig_free_prob_pct: float
    outcome_name: str
    is_sharp_source: bool
