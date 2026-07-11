from __future__ import annotations

from app.core.registry import Registry

# Import models so Alembic autogenerate + Base.metadata see the tables.
from app.modules.wiki import models  # noqa: F401


def register(registry: Registry) -> None:  # fleshed out in Task 3
    pass
