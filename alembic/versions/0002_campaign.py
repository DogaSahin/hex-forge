"""campaign table + default seed

Revision ID: 0002_campaign
Revises: 0001_baseline
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "0002_campaign"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    campaign = op.create_table(
        "campaign",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.bulk_insert(
        campaign,
        [{"name": "My Campaign", "created_at": datetime.now(UTC), "active": True}],
    )


def downgrade() -> None:
    op.drop_table("campaign")
