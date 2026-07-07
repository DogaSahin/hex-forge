from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app.core.campaigns import get_active_campaign, list_campaigns
from app.core.database import SessionLocal
from app.core.registry import NavItem

CORE_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def module_templates(module_dir: Path) -> Jinja2Templates:
    """A Jinja2Templates for a feature module: its own templates first, then core
    (so module templates can `{% extends "base.html" %}`)."""
    module_templates_dir = module_dir / "templates"
    tmpl = Jinja2Templates(directory=str(module_templates_dir))
    tmpl.env.loader = ChoiceLoader(
        [
            FileSystemLoader(str(module_templates_dir)),
            FileSystemLoader(str(CORE_TEMPLATES_DIR)),
        ]
    )
    return tmpl


def shell_context(request: Request) -> dict:
    """Nav + campaign context every full page needs. Moved verbatim from server.py."""
    registry = request.app.state.registry
    nav_items = [
        NavItem(label="Home", icon="home", url="/", order=0),
        *registry.sorted_nav(),
    ]
    db = SessionLocal()
    try:
        campaigns = list_campaigns(db)
        active = get_active_campaign(request, db)
        return {
            "nav_items": nav_items,
            "current_path": request.url.path,
            "campaigns": [{"id": c.id, "name": c.name} for c in campaigns],
            "active_campaign": {"id": active.id, "name": active.name} if active else None,
        }
    finally:
        db.close()
