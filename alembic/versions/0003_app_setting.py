"""app_setting table

Revision ID: 0003_app_setting
Revises: 0002_campaign
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_app_setting"
down_revision: str | None = "0002_campaign"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_setting",
        sa.Column("key", sa.String(length=200), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_setting")
