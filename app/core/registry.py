from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import APIRouter


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

    def add_router(self, router: APIRouter) -> None:
        self.routers.append(router)

    def add_nav(self, item: NavItem) -> None:
        self.nav_items.append(item)

    def add_ws_topics(self, topics: list[str]) -> None:
        self.ws_topics.extend(topics)

    def sorted_nav(self) -> list[NavItem]:
        return sorted(self.nav_items, key=lambda n: n.order)
