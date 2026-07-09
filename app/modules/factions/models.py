from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

DISPOSITIONS = ("hostile", "unfriendly", "neutral", "friendly", "allied")
DEFAULT_DISPOSITION = "neutral"


class Faction(Base):
    __tablename__ = "faction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    disposition: Mapped[str] = mapped_column(
        String(20), default=DEFAULT_DISPOSITION, server_default=DEFAULT_DISPOSITION, nullable=False
    )
    goals: Mapped[str | None] = mapped_column(Text)

    clocks: Mapped[list[FactionClock]] = relationship(
        back_populates="faction", cascade="all, delete-orphan", order_by="FactionClock.id"
    )

    activity: Mapped[list[FactionActivity]] = relationship(
        back_populates="faction",
        cascade="all, delete-orphan",
        order_by="FactionActivity.occurred_at.desc(), FactionActivity.id.desc()",
    )


class FactionClock(Base):
    __tablename__ = "faction_clock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("faction.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    segments: Mapped[int] = mapped_column(Integer, default=6, server_default="6", nullable=False)
    filled: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    faction: Mapped[Faction] = relationship(back_populates="clocks")


class FactionActivity(Base):
    __tablename__ = "faction_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("faction.id", ondelete="CASCADE"), index=True, nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    entry: Mapped[str] = mapped_column(Text, nullable=False)

    faction: Mapped[Faction] = relationship(back_populates="activity")
