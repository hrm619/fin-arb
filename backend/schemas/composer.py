"""Pydantic schemas for the estimate composer (Contract 4)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.schemas.confidence_scorer import CompositeConfidence
from backend.schemas.signal_aggregator import SignalAggregation


class StructuralAdjustmentDetail(BaseModel):
    edge_id: str
    metric: str
    applies_to_team: str
    edge_magnitude: float
    quality_grade: str | None
    quality_weight: float
    market_efficiency_discount: float
    adjustment: float


class SuggestedEstimateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    event_id: int
    anchor_prob_pct: float
    anchor_source: str
    structural_adjustments: list[StructuralAdjustmentDetail]
    total_structural_adjustment: float
    signal_aggregation: SignalAggregation | None
    total_signal_adjustment: float
    suggested_prob_pct: float
    composite_confidence: CompositeConfidence
    confidence_tier: str
