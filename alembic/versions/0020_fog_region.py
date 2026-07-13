"""fog_region table

Revision ID: 0020_fog_region
Revises: 0019_token
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_fog_region"
down_revision: str | None = "0019_token"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fog_region",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("map_id", sa.Integer(), sa.ForeignKey("map.id"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("op", sa.String(length=10), nullable=False),
        sa.Column("geom_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_fog_region_map_id", "fog_region", ["map_id"])


def downgrade() -> None:
    op.drop_index("ix_fog_region_map_id", table_name="fog_region")
    op.drop_table("fog_region")
