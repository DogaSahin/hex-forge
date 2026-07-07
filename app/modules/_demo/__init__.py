from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.registry import NavItem, Registry

router = APIRouter(prefix="/_demo")


@router.get("", response_class=HTMLResponse)
def demo_index() -> HTMLResponse:
    return HTMLResponse("<p id='demo'>Demo module registered ✔</p>")


def register(registry: Registry) -> None:
    registry.add_router(router)
    registry.add_nav(NavItem(label="Demo", icon="sparkles", url="/_demo", order=900))
