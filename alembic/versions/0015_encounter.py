"""encounter table

Revision ID: 0015_encounter
Revises: 0014_wiki_page_tag
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_encounter"
down_revision: str | None = "0014_wiki_page_tag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "encounter",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active_combatant_id", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.create_index("ix_encounter_campaign_id", "encounter", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_encounter_campaign_id", table_name="encounter")
    op.drop_table("encounter")
