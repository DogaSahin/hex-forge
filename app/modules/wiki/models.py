from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WikiPage(Base):
    __tablename__ = "wiki_page"
    __table_args__ = (UniqueConstraint("campaign_id", "slug", name="uq_wiki_page_campaign_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False)
    body_md: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(80), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )


class WikiLink(Base):
    __tablename__ = "wiki_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Real FK — same module. Rows are rebuilt on every save of the source page.
    source_page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wiki_page.id"), index=True, nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # page | npc | faction
    # Soft-ref (no FK to npc/faction — module independence). NULL = unresolved.
    target_id: Mapped[int | None] = mapped_column(Integer, index=True)
    target_title: Mapped[str] = mapped_column(String(200), nullable=False)  # raw [[Name]]


class Tag(Base):
    __tablename__ = "tag"
    __table_args__ = (UniqueConstraint("campaign_id", "name", name="uq_tag_campaign_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)


class WikiPageTag(Base):
    __tablename__ = "wiki_page_tag"

    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("wiki_page.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tag.id"), primary_key=True)
