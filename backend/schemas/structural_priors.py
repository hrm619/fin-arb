"""Pydantic schemas for structural priors responses."""

from pydantic import BaseModel, ConfigDict


class ApplicableEdge(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    edge_id: str
    hypothesis_name: str
    metric: str
    bucket_label: str
    edge_magnitude: float
    quality_grade: str | None = None
    quality_composite: float | None = None
    applies_to_team: str
    metric_value: float | None = None


class StructuralPriorsResponse(BaseModel):
    event_id: int
    edges: list[ApplicableEdge]
    total_structural_adjustment: float
