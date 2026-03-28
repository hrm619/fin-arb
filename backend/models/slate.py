"""Slate model — weekly event collections."""

from datetime import date, datetime

from sqlalchemy import Date, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Slate(Base):
    __tablename__ = "slates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        back_populates="slate", cascade="all, delete-orphan"
    )
