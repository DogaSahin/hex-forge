from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.dice.routes import router


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="Dice", icon="dice", url="/dice", order=800))
