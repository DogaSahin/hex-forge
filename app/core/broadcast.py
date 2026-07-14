from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base
from app.core.websocket import manager

BROADCAST_TOPIC = "broadcast"


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


def get_state(db: Session, campaign_id: int) -> BroadcastState:
    """Get-or-create the single broadcast row for a campaign."""
    state = db.query(BroadcastState).filter_by(campaign_id=campaign_id).first()
    if state is None:
        state = BroadcastState(campaign_id=campaign_id)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def set_active_encounter(db: Session, campaign_id: int, encounter_id: int | None) -> BroadcastState:
    state = get_state(db, campaign_id)
    state.active_encounter_id = encounter_id
    db.commit()
    db.refresh(state)
    return state


def set_active_map(db: Session, campaign_id: int, map_id: int | None) -> BroadcastState:
    state = get_state(db, campaign_id)
    state.active_map_id = map_id
    db.commit()
    db.refresh(state)
    return state


def snapshot(db: Session, campaign_id: int) -> dict:
    """The player-visible pointer state — ids only, never module content."""
    state = get_state(db, campaign_id)
    return {
        "active_encounter_id": state.active_encounter_id,
        "active_map_id": state.active_map_id,
    }


async def publish_changed(campaign_id: int) -> None:
    """Contentless signal: the player refetches its own snapshot on receipt."""
    await manager.publish(
        BROADCAST_TOPIC, {"action": "broadcast_changed", "campaign_id": campaign_id}
    )
