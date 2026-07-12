from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi import APIRouter

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

EntityProvider = Callable[["Session", int], "list[tuple[int, str]]"]
DetailProvider = Callable[["Session", int, int], "dict | None"]
JumpProvider = Callable[["Session", int], "list[dict]"]


@dataclass(frozen=True)
class NavItem:
    label: str
    icon: str
    url: str
    order: int = 100


@dataclass
class Registry:
    routers: list[APIRouter] = field(default_factory=list)
    nav_items: list[NavItem] = field(default_factory=list)
    ws_topics: list[str] = field(default_factory=list)
    entity_providers: dict[str, EntityProvider] = field(default_factory=dict)
    entity_detail_providers: dict[str, DetailProvider] = field(default_factory=dict)
    jump_providers: dict[str, JumpProvider] = field(default_factory=dict)

    def add_router(self, router: APIRouter) -> None:
        self.routers.append(router)

    def add_nav(self, item: NavItem) -> None:
        self.nav_items.append(item)

    def add_ws_topics(self, topics: list[str]) -> None:
        self.ws_topics.extend(topics)

    def sorted_nav(self) -> list[NavItem]:
        return sorted(self.nav_items, key=lambda n: n.order)

    def add_entity_provider(self, kind: str, provider: EntityProvider) -> None:
        self.entity_providers[kind] = provider

    def entities(self, kind: str, db, campaign_id: int) -> list[tuple[int, str]]:
        provider = self.entity_providers.get(kind)
        return provider(db, campaign_id) if provider else []

    def resolve(self, kind: str, entity_id: int, db, campaign_id: int) -> str | None:
        for eid, name in self.entities(kind, db, campaign_id):
            if eid == entity_id:
                return name
        return None

    def add_entity_detail_provider(self, kind: str, provider: DetailProvider) -> None:
        self.entity_detail_providers[kind] = provider

    def entity_detail(self, kind: str, entity_id: int, db, campaign_id: int) -> dict | None:
        provider = self.entity_detail_providers.get(kind)
        return provider(db, entity_id, campaign_id) if provider else None

    def add_jump_provider(self, kind: str, provider: JumpProvider) -> None:
        self.jump_providers[kind] = provider

    def jump_targets(self, db, campaign_id: int) -> list[dict]:
        targets: list[dict] = []
        for provider in self.jump_providers.values():
            targets.extend(provider(db, campaign_id))
        return targets
