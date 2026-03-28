"""Pydantic schemas for Signal request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SignalData(BaseModel):
    """Structured signal parsed from LLM response."""
    signal_type: str
    content: str
    relevance_score: float
    timestamp_ref: str | None = None


class SignalFlagUpdate(BaseModel):
    user_flag: str  # "used_in_pricing" or "dismissed"


class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transcript_id: int
    event_id: int
    signal_type: str
    content: str
    relevance_score: float | None
    timestamp_ref: str | None
    user_flag: str | None
    created_at: datetime
