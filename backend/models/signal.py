"""Signal model — LLM-extracted insights."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    transcript_id: Mapped[int] = mapped_column(
        ForeignKey("transcripts.id"), nullable=False
    )
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    signal_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[Optional[float]] = mapped_column(default=None)
    timestamp_ref: Mapped[Optional[str]] = mapped_column(String, default=None)
    direction: Mapped[Optional[int]] = mapped_column(default=None)
    user_flag: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    transcript: Mapped["Transcript"] = relationship(  # noqa: F821
        back_populates="signals"
    )
    event: Mapped["Event"] = relationship(back_populates="signals")  # noqa: F821
