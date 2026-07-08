from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SavedRoll(Base):
    __tablename__ = "saved_roll"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    expression: Mapped[str] = mapped_column(String(200), nullable=False)


class RollHistory(Base):
    __tablename__ = "roll_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    expression: Mapped[str] = mapped_column(String(200), nullable=False)
    result: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    rolled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
