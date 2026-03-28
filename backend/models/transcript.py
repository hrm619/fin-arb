"""Transcript model — audio/transcript data."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String, default=None)
    source_type: Mapped[str] = mapped_column(String, default="youtube")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_secs: Mapped[Optional[int]] = mapped_column(default=None)
    processed_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    event: Mapped["Event"] = relationship(back_populates="transcripts")  # noqa: F821
    signals: Mapped[list["Signal"]] = relationship(  # noqa: F821
        back_populates="transcript", cascade="all, delete-orphan"
    )
