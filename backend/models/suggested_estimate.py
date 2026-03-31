"""SuggestedEstimate model — system-generated probability estimates."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class SuggestedEstimate(Base):
    __tablename__ = "suggested_estimates"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"), nullable=False, unique=True
    )
    anchor_prob_pct: Mapped[float] = mapped_column(nullable=False)
    anchor_source: Mapped[str] = mapped_column(nullable=False)
    structural_adjustment: Mapped[float] = mapped_column(default=0.0)
    signal_adjustment: Mapped[float] = mapped_column(default=0.0)
    suggested_prob_pct: Mapped[float] = mapped_column(nullable=False)
    composite_confidence: Mapped[float] = mapped_column(nullable=False)
    confidence_tier: Mapped[str] = mapped_column(nullable=False)
    decomposition_json: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    event: Mapped["Event"] = relationship(back_populates="suggested_estimate")  # noqa: F821
