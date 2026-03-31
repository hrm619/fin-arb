"""Pydantic schemas for composite confidence scoring."""

from pydantic import BaseModel


class CompositeConfidence(BaseModel):
    structural_strength: float
    signal_coherence: float
    line_confirmation: float
    composite_score: float
    tier: str  # "high", "medium", "low"
    weights_used: dict[str, float]
