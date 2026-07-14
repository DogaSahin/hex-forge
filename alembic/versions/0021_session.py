"""session table

Revision ID: 0021_session
Revises: 0020_fog_region
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021_session"
down_revision: str | None = "0020_fog_region"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "session",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="planned"),
    )
    op.create_index("ix_session_campaign_id", "session", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_session_campaign_id", table_name="session")
    op.drop_table("session")
