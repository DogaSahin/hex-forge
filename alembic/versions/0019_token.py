"""token table

Revision ID: 0019_token
Revises: 0018_map
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019_token"
down_revision: str | None = "0018_map"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "token",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("map_id", sa.Integer(), sa.ForeignKey("map.id"), nullable=False),
        sa.Column("layer", sa.String(length=20), nullable=False, server_default="tokens"),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="disc"),
        sa.Column("x", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("y", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("color", sa.String(length=20)),
        sa.Column("image_path", sa.String(length=500)),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("hp_current", sa.Integer()),
        sa.Column("hp_max", sa.Integer()),
        sa.Column("hp_visible_to_players", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("visible_to_players", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("meta_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_token_map_id", "token", ["map_id"])


def downgrade() -> None:
    op.drop_index("ix_token_map_id", table_name="token")
    op.drop_table("token")
