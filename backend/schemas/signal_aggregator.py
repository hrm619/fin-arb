"""Pydantic schemas for signal aggregation responses."""

from pydantic import BaseModel


class SignalContribution(BaseModel):
    signal_id: int
    signal_type: str
    direction: int
    relevance_score: float
    cap: float
    adjustment: float


class SignalAggregation(BaseModel):
    contributions: list[SignalContribution]
    total_adjustment: float
    signal_count: int
