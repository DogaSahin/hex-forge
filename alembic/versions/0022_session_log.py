"""session_log table

Revision ID: 0022_session_log
Revises: 0021_session
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_session_log"
down_revision: str | None = "0021_session"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "session_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("logged_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("tag", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_session_log_session_id", "session_log", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_session_log_session_id", table_name="session_log")
    op.drop_table("session_log")
