"""UserEstimate model — user probability submissions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class UserEstimate(Base):
    __tablename__ = "user_estimates"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"), nullable=False, unique=True
    )
    probability_pct: Mapped[float] = mapped_column(nullable=False)
    american_odds: Mapped[Optional[int]] = mapped_column(default=None)
    decimal_odds: Mapped[Optional[float]] = mapped_column(default=None)
    note: Mapped[Optional[str]] = mapped_column(Text, default=None)
    suggested_estimate_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suggested_estimates.id"), default=None
    )
    locked_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    event: Mapped["Event"] = relationship(back_populates="estimate")  # noqa: F821
