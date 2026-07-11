"""npc table

Revision ID: 0009_npc
Revises: 0008_faction_activity
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_npc"
down_revision: str | None = "0008_faction_activity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "npc",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("statblock", sa.Text()),
        sa.Column("motivation", sa.Text()),
        sa.Column("secrets", sa.Text()),
        sa.Column("voice", sa.Text()),
        sa.Column("portrait_path", sa.String(length=255)),
        sa.Column("faction_id", sa.Integer()),
        sa.Column("disposition", sa.String(length=20), nullable=False, server_default="neutral"),
    )
    op.create_index("ix_npc_campaign_id", "npc", ["campaign_id"])
    op.create_index("ix_npc_faction_id", "npc", ["faction_id"])


def downgrade() -> None:
    op.drop_index("ix_npc_faction_id", table_name="npc")
    op.drop_index("ix_npc_campaign_id", table_name="npc")
    op.drop_table("npc")
