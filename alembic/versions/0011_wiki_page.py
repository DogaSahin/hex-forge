"""wiki_page table

Revision ID: 0011_wiki_page
Revises: 0010_relationship
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_wiki_page"
down_revision: str | None = "0010_relationship"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_page",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("body_md", sa.Text()),
        sa.Column("category", sa.String(length=80)),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("campaign_id", "slug", name="uq_wiki_page_campaign_slug"),
    )
    op.create_index("ix_wiki_page_campaign_id", "wiki_page", ["campaign_id"])
    op.create_index("ix_wiki_page_category", "wiki_page", ["category"])


def downgrade() -> None:
    op.drop_index("ix_wiki_page_category", table_name="wiki_page")
    op.drop_index("ix_wiki_page_campaign_id", table_name="wiki_page")
    op.drop_table("wiki_page")
