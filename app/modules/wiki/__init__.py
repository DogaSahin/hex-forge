from __future__ import annotations

from app.core.registry import NavItem, Registry
from app.modules.wiki import models  # noqa: F401
from app.modules.wiki.routes import router, wiki_jump


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="Wiki", icon="book", url="/wiki", order=600))
    registry.add_jump_provider("wiki_page", wiki_jump)
