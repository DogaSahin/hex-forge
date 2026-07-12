"""combatant table

Revision ID: 0016_combatant
Revises: 0015_encounter
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_combatant"
down_revision: str | None = "0015_encounter"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "combatant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounter.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("initiative", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hp_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hp_max", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ac", sa.Integer()),
        sa.Column("conditions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("concentration", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_pc", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("npc_id", sa.Integer()),
        sa.Column("token_id", sa.Integer()),
    )
    op.create_index("ix_combatant_encounter_id", "combatant", ["encounter_id"])
    op.create_index("ix_combatant_npc_id", "combatant", ["npc_id"])
    op.create_index("ix_combatant_token_id", "combatant", ["token_id"])


def downgrade() -> None:
    op.drop_index("ix_combatant_token_id", table_name="combatant")
    op.drop_index("ix_combatant_npc_id", table_name="combatant")
    op.drop_index("ix_combatant_encounter_id", table_name="combatant")
    op.drop_table("combatant")
