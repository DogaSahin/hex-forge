from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.sessions.routes import router


def register(registry: Registry) -> None:
    registry.add_router(router)
    # Rail order per spec §8: Home 0, Combat 200, Maps 300, NPCs 400,
    # Factions 500, Wiki 600, Sessions 700, Dice 800.
    registry.add_nav(NavItem(label="Sessions", icon="scroll", url="/sessions", order=700))
