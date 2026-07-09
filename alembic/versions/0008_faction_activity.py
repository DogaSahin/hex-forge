"""faction_activity table

Revision ID: 0008_faction_activity
Revises: 0007_faction_clock
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_faction_activity"
down_revision: str | None = "0007_faction_clock"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faction_activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "faction_id",
            sa.Integer(),
            sa.ForeignKey("faction.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("entry", sa.Text(), nullable=False),
    )
    op.create_index("ix_faction_activity_faction_id", "faction_activity", ["faction_id"])


def downgrade() -> None:
    op.drop_index("ix_faction_activity_faction_id", table_name="faction_activity")
    op.drop_table("faction_activity")
