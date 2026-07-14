"""map table

Revision ID: 0018_map
Revises: 0017_broadcast_state
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_map"
down_revision: str | None = "0017_broadcast_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "map",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("image_path", sa.String(length=500)),
        sa.Column("image_w", sa.Integer()),
        sa.Column("image_h", sa.Integer()),
        sa.Column("grid_size_px", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("grid_offset_x", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grid_offset_y", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grid_visible", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("feet_per_square", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "diagonal_rule",
            sa.String(length=20),
            nullable=False,
            server_default="chebyshev",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.create_index("ix_map_campaign_id", "map", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_map_campaign_id", table_name="map")
    op.drop_table("map")
