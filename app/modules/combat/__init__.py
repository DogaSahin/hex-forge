from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.combat.routes import encounter_jump, router


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="Combat", icon="swords", url="/combat", order=200))
    registry.add_ws_topics(["combat:{id}"])
    registry.add_jump_provider("encounter", encounter_jump)
