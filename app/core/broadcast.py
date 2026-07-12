from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BroadcastState(Base):
    """Per-campaign singleton of what the player screen currently mirrors.

    active_encounter_id / active_map_id are soft-refs (no FK) so core stays
    independent of the combat/map schemas; a dangling id means 'nothing active'.
    active_map_id is inert until Epic 8.
    """

    __tablename__ = "broadcast_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), unique=True, index=True, nullable=False
    )
    active_encounter_id: Mapped[int | None] = mapped_column(Integer)
    active_map_id: Mapped[int | None] = mapped_column(Integer)
