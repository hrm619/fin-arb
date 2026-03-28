"""Event model — individual predictions/bets."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    slate_id: Mapped[int] = mapped_column(ForeignKey("slates.id"), nullable=False)
    home_team: Mapped[str] = mapped_column(String, nullable=False)
    away_team: Mapped[str] = mapped_column(String, nullable=False)
    sport: Mapped[str] = mapped_column(String, nullable=False)
    league: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[datetime] = mapped_column(nullable=False)
    market_type: Mapped[str] = mapped_column(String, nullable=False)
    spread_value: Mapped[Optional[float]] = mapped_column(default=None)
    total_value: Mapped[Optional[float]] = mapped_column(default=None)
    confidence_tier: Mapped[Optional[str]] = mapped_column(String, default=None)
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    slate: Mapped["Slate"] = relationship(back_populates="events")  # noqa: F821
    transcripts: Mapped[list["Transcript"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    signals: Mapped[list["Signal"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    estimate: Mapped[Optional["UserEstimate"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan", uselist=False
    )
    market_lines: Mapped[list["MarketLine"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    outcome: Mapped[Optional["Outcome"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan", uselist=False
    )
