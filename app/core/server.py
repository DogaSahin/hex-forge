from __future__ import annotations

import importlib
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core import config
from app.core.campaigns import COOKIE_NAME, get_active_campaign, list_campaigns
from app.core.database import SessionLocal
from app.core.registry import NavItem, Registry

CORE_DIR = Path(__file__).resolve().parent
STATIC_DIR = CORE_DIR / "static"
TEMPLATES_DIR = CORE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def shell_context(request: Request) -> dict:
    registry = request.app.state.registry
    nav_items = [
        NavItem(label="Home", icon="home", url="/", order=0),
        *registry.sorted_nav(),
    ]
    db = SessionLocal()
    try:
        campaigns = list_campaigns(db)
        active = get_active_campaign(request, db)
        # detach ids/names the template needs before the session closes
        return {
            "nav_items": nav_items,
            "current_path": request.url.path,
            "campaigns": [{"id": c.id, "name": c.name} for c in campaigns],
            "active_campaign": {"id": active.id, "name": active.name} if active else None,
        }
    finally:
        db.close()


def build_registry() -> Registry:
    registry = Registry()
    for dotted_path in config.ENABLED_MODULES:
        module = importlib.import_module(dotted_path)
        module.register(registry)
    return registry


def create_app() -> FastAPI:
    app = FastAPI(title="Hexforge")

    registry = build_registry()
    app.state.registry = registry
    for router in registry.routers:
        app.include_router(router)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "home.html", shell_context(request))

    @app.get("/style", response_class=HTMLResponse)
    def style(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "style.html", shell_context(request))

    @app.post("/campaign/switch")
    def switch_campaign(campaign_id: str = Form(...)) -> RedirectResponse:
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie(COOKIE_NAME, campaign_id, httponly=True, samesite="lax")
        return resp

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/smoke", response_class=HTMLResponse)
    def smoke(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "smoke.html", {"count_start": 0})

    @app.get("/smoke/fragment", response_class=HTMLResponse)
    def smoke_fragment() -> HTMLResponse:
        return HTMLResponse("<p id='swapped'>Swapped by HTMX ✔</p>")

    return app
