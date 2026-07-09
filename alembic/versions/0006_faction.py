"""faction table

Revision ID: 0006_faction
Revises: 0005_roll_history
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_faction"
down_revision: str | None = "0005_roll_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faction",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("disposition", sa.String(length=20), nullable=False, server_default="neutral"),
        sa.Column("goals", sa.Text(), nullable=True),
    )
    op.create_index("ix_faction_campaign_id", "faction", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_faction_campaign_id", table_name="faction")
    op.drop_table("faction")
