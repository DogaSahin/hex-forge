"""roll_history table

Revision ID: 0005_roll_history
Revises: 0004_saved_roll
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_roll_history"
down_revision: str | None = "0004_saved_roll"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roll_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("campaign.id"),
            nullable=False,
        ),
        sa.Column("expression", sa.String(length=200), nullable=False),
        sa.Column("result", sa.Integer(), nullable=False),
        sa.Column("breakdown_json", sa.Text(), nullable=False),
        sa.Column(
            "rolled_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_roll_history_campaign_id", "roll_history", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_roll_history_campaign_id", table_name="roll_history")
    op.drop_table("roll_history")
