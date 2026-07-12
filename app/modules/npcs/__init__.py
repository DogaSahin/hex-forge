from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.npcs.routes import npc_jump, register_entities, router


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="NPCs", icon="users", url="/npcs", order=400))
    register_entities(registry)
    registry.add_jump_provider("npc", npc_jump)
