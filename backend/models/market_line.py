"""MarketLine model — odds from multiple sources."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class MarketLine(Base):
    __tablename__ = "market_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    market_key: Mapped[Optional[str]] = mapped_column(String, default=None)
    implied_prob_pct: Mapped[float] = mapped_column(nullable=False)
    american_odds: Mapped[Optional[int]] = mapped_column(default=None)
    decimal_odds: Mapped[Optional[float]] = mapped_column(default=None)
    fetched_at: Mapped[datetime] = mapped_column(nullable=False)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, default=None)

    event: Mapped["Event"] = relationship(back_populates="market_lines")  # noqa: F821
