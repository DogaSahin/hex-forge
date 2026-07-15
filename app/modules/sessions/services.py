from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.sessions.models import GameSession, SessionLog


def next_number(db: Session, campaign_id: int) -> int:
    """Session numbers run per campaign, not globally."""
    top = (
        db.query(func.max(GameSession.number))
        .filter(GameSession.campaign_id == campaign_id)
        .scalar()
    )
    return (top or 0) + 1


def activate(db: Session, session_row: GameSession) -> None:
    """Exactly one active session per campaign: activating demotes the incumbent.

    Enforced here rather than with a DB constraint — a partial unique index buys
    little on SQLite and fights Alembic.
    """
    db.query(GameSession).filter(
        GameSession.campaign_id == session_row.campaign_id,
        GameSession.status == "active",
        GameSession.id != session_row.id,
    ).update({"status": "done"}, synchronize_session=False)
    session_row.status = "active"
    db.commit()


def owned(db: Session, session_id: int, campaign_id: int) -> GameSession | None:
    row = db.get(GameSession, session_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def owned_log(db: Session, log_id: int, campaign_id: int) -> SessionLog | None:
    log = db.get(SessionLog, log_id)
    if log is None or log.session.campaign_id != campaign_id:
        return None
    return log


def roster(db: Session, campaign_id: int) -> list[GameSession]:
    return (
        db.query(GameSession)
        .filter_by(campaign_id=campaign_id)
        .order_by(GameSession.number.desc())
        .all()
    )
