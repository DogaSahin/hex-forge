from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CONDITIONS = (
    "blinded",
    "charmed",
    "deafened",
    "frightened",
    "grappled",
    "incapacitated",
    "invisible",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious",
)


class Encounter(Base):
    __tablename__ = "encounter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    # Soft-ref (no FK — avoids a circular FK with combatant). NULL = combat not started.
    active_combatant_id: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )


class Combatant(Base):
    __tablename__ = "combatant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    encounter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("encounter.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    initiative: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    hp_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    hp_max: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    ac: Mapped[int | None] = mapped_column(Integer)
    conditions_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]", server_default="[]"
    )
    concentration: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_pc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    # Soft-refs (no FK — drop-in module independence). token_id is inert until Epic 8.
    npc_id: Mapped[int | None] = mapped_column(Integer, index=True)
    token_id: Mapped[int | None] = mapped_column(Integer, index=True)
