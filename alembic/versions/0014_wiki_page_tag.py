"""wiki_page_tag join table

Revision ID: 0014_wiki_page_tag
Revises: 0013_tag
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_wiki_page_tag"
down_revision: str | None = "0013_tag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_page_tag",
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("wiki_page.id"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tag.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("wiki_page_tag")
