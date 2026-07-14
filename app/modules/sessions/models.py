from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# NB: `date` is imported as `date_type` because the model has a column *named*
# `date`. Annotating `date: Mapped[date]` makes SQLAlchemy resolve the annotation
# against a name the class body has already rebound — an avoidable trap.

STATUSES = ("planned", "active", "done")
DEFAULT_STATUS = "planned"

# "none" is an untagged line: it shows in the feed but is skipped by the recap.
TAGS = ("none", "combat", "roleplay", "loot", "thread")
DEFAULT_TAG = "none"
THREAD_TAG = "thread"


class GameSession(Base):
    # NB: the class is GameSession, not Session — `Session` is sqlalchemy.orm.Session,
    # which every routes module imports. The table is still `session`.
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date_type] = mapped_column(
        Date, default=lambda: datetime.now(UTC).date(), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default=DEFAULT_STATUS, server_default=DEFAULT_STATUS, nullable=False
    )

    logs: Mapped[list[SessionLog]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionLog.logged_at.desc(), SessionLog.id.desc()",
    )


class SessionLog(Base):
    __tablename__ = "session_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("session.id", ondelete="CASCADE"), index=True, nullable=False
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tag: Mapped[str] = mapped_column(
        String(20), default=DEFAULT_TAG, server_default=DEFAULT_TAG, nullable=False
    )
    # Only meaningful for THREAD_TAG rows. NULL = the thread is still open.
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    session: Mapped[GameSession] = relationship(back_populates="logs")
