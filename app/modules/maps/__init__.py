from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.maps.routes import map_jump, router, token_router


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_router(token_router)
    registry.add_nav(NavItem(label="Maps", icon="map", url="/map", order=300))
    registry.add_ws_topics(["map:{id}", "map:{id}:dm"])
    registry.add_jump_provider("map", map_jump)
