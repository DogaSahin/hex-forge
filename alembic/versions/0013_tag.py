"""tag table

Revision ID: 0013_tag
Revises: 0012_wiki_link
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_tag"
down_revision: str | None = "0012_wiki_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.UniqueConstraint("campaign_id", "name", name="uq_tag_campaign_name"),
    )
    op.create_index("ix_tag_campaign_id", "tag", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_tag_campaign_id", table_name="tag")
    op.drop_table("tag")
