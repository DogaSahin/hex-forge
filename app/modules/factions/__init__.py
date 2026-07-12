from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.factions.routes import faction_entities, faction_jump, router


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="Factions", icon="flag", url="/factions", order=500))
    registry.add_entity_provider("faction", faction_entities)
    registry.add_jump_provider("faction", faction_jump)
