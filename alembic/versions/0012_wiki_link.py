"""wiki_link table

Revision ID: 0012_wiki_link
Revises: 0011_wiki_page
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_wiki_link"
down_revision: str | None = "0011_wiki_page"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_link",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_page_id", sa.Integer(), sa.ForeignKey("wiki_page.id"), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Integer()),
        sa.Column("target_title", sa.String(length=200), nullable=False),
    )
    op.create_index("ix_wiki_link_source_page_id", "wiki_link", ["source_page_id"])
    op.create_index("ix_wiki_link_target_id", "wiki_link", ["target_id"])


def downgrade() -> None:
    op.drop_index("ix_wiki_link_target_id", table_name="wiki_link")
    op.drop_index("ix_wiki_link_source_page_id", table_name="wiki_link")
    op.drop_table("wiki_link")
