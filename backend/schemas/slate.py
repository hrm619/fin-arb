"""Pydantic schemas for Slate request/response models."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SlateCreate(BaseModel):
    name: str
    week_start: date
    week_end: date


class SlateUpdate(BaseModel):
    name: str | None = None
    week_start: date | None = None
    week_end: date | None = None


class SlateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    week_start: date
    week_end: date
    created_at: datetime
    updated_at: datetime


class SlateDetailResponse(SlateResponse):
    events: list["EventResponse"] = []


from backend.schemas.event import EventResponse  # noqa: E402

SlateDetailResponse.model_rebuild()
