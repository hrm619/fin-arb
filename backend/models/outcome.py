"""Outcome model — graded event results."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"), nullable=False, unique=True
    )
    result: Mapped[str] = mapped_column(String, nullable=False)
    actual_score: Mapped[Optional[str]] = mapped_column(String, default=None)
    graded_at: Mapped[datetime] = mapped_column(nullable=False)
    graded_by: Mapped[str] = mapped_column(String, default="user")
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)

    event: Mapped["Event"] = relationship(back_populates="outcome")  # noqa: F821
