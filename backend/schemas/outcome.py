"""Pydantic schemas for Outcome/Tracking request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OutcomeCreate(BaseModel):
    result: str  # win, loss, push
    actual_score: str | None = None
    notes: str | None = None


class OutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    result: str
    actual_score: str | None
    graded_at: datetime
    graded_by: str
    notes: str | None


class TrackingSummary(BaseModel):
    total_graded: int
    wins: int
    losses: int
    pushes: int
    hit_rate: float
    roi: float


class EdgeBreakdown(BaseModel):
    dimension: str
    group: str
    count: int
    hit_rate: float
    avg_edge: float
