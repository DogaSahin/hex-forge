from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.registry import DashboardCard, Metric
from app.core.templating import module_templates
from app.modules.sessions.models import THREAD_TAG, GameSession, SessionLog

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

THREAD_LIMIT = 8
SUMMARY_EXCERPT_CHARS = 400


def _open_threads(db: Session, campaign_id: int) -> list[SessionLog]:
    return (
        db.query(SessionLog)
        .join(GameSession)
        .filter(
            GameSession.campaign_id == campaign_id,
            SessionLog.tag == THREAD_TAG,
            SessionLog.resolved_at.is_(None),
        )
        .order_by(SessionLog.logged_at.desc(), SessionLog.id.desc())
        .limit(THREAD_LIMIT)
        .all()
    )


def _open_thread_count(db: Session, campaign_id: int) -> int:
    return (
        db.query(SessionLog)
        .join(GameSession)
        .filter(
            GameSession.campaign_id == campaign_id,
            SessionLog.tag == THREAD_TAG,
            SessionLog.resolved_at.is_(None),
        )
        .count()
    )


def _last_done_session(db: Session, campaign_id: int) -> GameSession | None:
    return (
        db.query(GameSession)
        .filter(GameSession.campaign_id == campaign_id, GameSession.status == "done")
        .order_by(GameSession.number.desc())
        .first()
    )


def _active_session(db: Session, campaign_id: int) -> GameSession | None:
    return (
        db.query(GameSession)
        .filter(GameSession.campaign_id == campaign_id, GameSession.status == "active")
        .first()
    )


def render_threads_card(db: Session, campaign_id: int) -> str:
    return templates.env.get_template("_card_threads.html").render(
        threads=_open_threads(db, campaign_id)
    )


def render_last_session_card(db: Session, campaign_id: int) -> str:
    row = _last_done_session(db, campaign_id)
    excerpt = None
    if row is not None and row.summary:
        excerpt = row.summary[:SUMMARY_EXCERPT_CHARS]
        if len(row.summary) > SUMMARY_EXCERPT_CHARS:
            excerpt += "…"
    return templates.env.get_template("_card_last_session.html").render(
        session=row, excerpt=excerpt
    )


def session_metrics(db: Session, campaign_id: int) -> list[Metric]:
    current = _active_session(db, campaign_id) or _last_done_session(db, campaign_id)
    return [
        Metric(
            label="Session",
            value=f"#{current.number}" if current else "—",
            href="/sessions",
            order=100,
        ),
        Metric(
            label="Open threads",
            value=str(_open_thread_count(db, campaign_id)),
            href="/sessions",
            order=200,
        ),
    ]


CARDS: list[DashboardCard] = [
    DashboardCard(
        key="sessions.threads", title="Open threads", render=render_threads_card, order=300
    ),
    DashboardCard(
        key="sessions.last",
        title="Last session",
        render=render_last_session_card,
        order=400,
        span=2,
    ),
]
