from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.registry import DashboardCard, Metric
from app.core.templating import module_templates
from app.modules.factions.models import Faction, FactionActivity, FactionClock

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

ACTIVITY_LIMIT = 8
CLOCK_LIMIT = 6
# A clock at half fill or more is "near completion". Fully-filled clocks stay on the
# card on purpose: a fired clock is the most urgent thing on the board.
NEAR_COMPLETE_RATIO = 0.5


def render_activity_card(db: Session, campaign_id: int) -> str:
    rows = (
        db.query(FactionActivity)
        .join(Faction)
        .filter(Faction.campaign_id == campaign_id)
        .order_by(FactionActivity.occurred_at.desc(), FactionActivity.id.desc())
        .limit(ACTIVITY_LIMIT)
        .all()
    )
    return templates.env.get_template("_card_activity.html").render(rows=rows)


def _near_complete_clocks(db: Session, campaign_id: int) -> list[FactionClock]:
    clocks = (
        db.query(FactionClock)
        .join(Faction)
        .filter(Faction.campaign_id == campaign_id, FactionClock.filled > 0)
        .all()
    )
    near = [c for c in clocks if c.filled / c.segments >= NEAR_COMPLETE_RATIO]
    near.sort(key=lambda c: c.filled / c.segments, reverse=True)
    return near[:CLOCK_LIMIT]


def render_clocks_card(db: Session, campaign_id: int) -> str:
    return templates.env.get_template("_card_clocks.html").render(
        clocks=_near_complete_clocks(db, campaign_id)
    )


def faction_metrics(db: Session, campaign_id: int) -> list[Metric]:
    active = (
        db.query(FactionClock)
        .join(Faction)
        .filter(
            Faction.campaign_id == campaign_id,
            FactionClock.filled > 0,
            FactionClock.filled < FactionClock.segments,
        )
        .count()
    )
    return [Metric(label="Active clocks", value=str(active), href="/factions", order=300)]


CARDS: list[DashboardCard] = [
    DashboardCard(
        key="factions.activity",
        title="Recent faction moves",
        render=render_activity_card,
        order=100,
    ),
    DashboardCard(
        key="factions.clocks",
        title="Clocks near completion",
        render=render_clocks_card,
        order=200,
    ),
]
