# hex-forge/alembic/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the project root (hex-forge/) importable so `app...` resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Every module's models must be imported below so its tables land on Base.metadata.
# A module missing from this list is invisible to autogenerate, which then reads its
# tables as deleted and emits drop_table for them.
from app.core import broadcast as core_broadcast  # noqa: E402,F401
from app.core import config as app_config  # noqa: E402
from app.core import models  # noqa: E402,F401  (register tables on Base.metadata)
from app.core.database import Base  # noqa: E402
from app.modules.combat import models as combat_models  # noqa: E402,F401
from app.modules.dice import models as dice_models  # noqa: E402,F401
from app.modules.factions import models as factions_models  # noqa: E402,F401
from app.modules.maps import models as maps_models  # noqa: E402,F401
from app.modules.npcs import models as npcs_models  # noqa: E402,F401
from app.modules.sessions import models as sessions_models  # noqa: E402,F401
from app.modules.wiki import models as wiki_models  # noqa: E402,F401

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    os.environ.get("HEXFORGE_DB_URL", app_config.DB_URL),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
