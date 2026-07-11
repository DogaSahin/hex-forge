from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DISPOSITIONS = ("hostile", "unfriendly", "neutral", "friendly", "allied")
DEFAULT_DISPOSITION = "neutral"


class Npc(Base):
    __tablename__ = "npc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    statblock: Mapped[str | None] = mapped_column(Text)
    motivation: Mapped[str | None] = mapped_column(Text)
    secrets: Mapped[str | None] = mapped_column(Text)
    voice: Mapped[str | None] = mapped_column(Text)
    portrait_path: Mapped[str | None] = mapped_column(String(255))
    # Soft cross-module reference to faction.id — no DB FK (module independence).
    faction_id: Mapped[int | None] = mapped_column(Integer, index=True)
    disposition: Mapped[str] = mapped_column(
        String(20), default=DEFAULT_DISPOSITION, server_default=DEFAULT_DISPOSITION, nullable=False
    )
