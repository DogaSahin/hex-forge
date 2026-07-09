"""saved_roll table

Revision ID: 0004_saved_roll
Revises: 0003_app_setting
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_saved_roll"
down_revision: str | None = "0003_app_setting"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_roll",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("campaign.id"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("expression", sa.String(length=200), nullable=False),
    )
    op.create_index("ix_saved_roll_campaign_id", "saved_roll", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_saved_roll_campaign_id", table_name="saved_roll")
    op.drop_table("saved_roll")
