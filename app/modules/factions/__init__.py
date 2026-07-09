from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.factions.routes import router


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="Factions", icon="flag", url="/factions", order=500))
