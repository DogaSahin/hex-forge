"""relationship table

Revision ID: 0010_relationship
Revises: 0009_npc
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_relationship"
down_revision: str | None = "0009_npc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relationship",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_relationship_campaign_id", "relationship", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_relationship_campaign_id", table_name="relationship")
    op.drop_table("relationship")
