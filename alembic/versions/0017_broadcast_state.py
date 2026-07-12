"""broadcast_state table

Revision ID: 0017_broadcast_state
Revises: 0016_combatant
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_broadcast_state"
down_revision: str | None = "0016_combatant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broadcast_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("active_encounter_id", sa.Integer()),
        sa.Column("active_map_id", sa.Integer()),
    )
    op.create_index(
        "ix_broadcast_state_campaign_id", "broadcast_state", ["campaign_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_broadcast_state_campaign_id", table_name="broadcast_state")
    op.drop_table("broadcast_state")
