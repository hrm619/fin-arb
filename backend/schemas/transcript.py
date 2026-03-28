"""Pydantic schemas for Transcript request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TranscriptIngestURL(BaseModel):
    source_url: str


class TranscriptIngestText(BaseModel):
    raw_text: str
    source_url: str | None = None


class TranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    source_url: str | None
    source_type: str
    raw_text: str
    duration_secs: int | None
    processed_at: datetime | None
    created_at: datetime
