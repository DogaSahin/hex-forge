"""faction_clock table

Revision ID: 0007_faction_clock
Revises: 0006_faction
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_faction_clock"
down_revision: str | None = "0006_faction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faction_clock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "faction_id",
            sa.Integer(),
            sa.ForeignKey("faction.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("segments", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("filled", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_faction_clock_faction_id", "faction_clock", ["faction_id"])


def downgrade() -> None:
    op.drop_index("ix_faction_clock_faction_id", table_name="faction_clock")
    op.drop_table("faction_clock")
