from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.maps.models import Map

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/map")


def _maps(db: Session, campaign_id: int) -> list[Map]:
    return db.query(Map).filter_by(campaign_id=campaign_id).order_by(Map.name).all()


def _owned_map(db: Session, map_id: int, campaign_id: int) -> Map | None:
    m = db.get(Map, map_id)
    return m if m is not None and m.campaign_id == campaign_id else None


def map_jump(db: Session, campaign_id: int) -> list[dict]:
    return [{"label": m.name, "url": f"/map/{m.id}", "kind": "map"} for m in _maps(db, campaign_id)]


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    maps = _maps(db, campaign.id)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request, "_map_list.html", {"maps": maps, "active_id": None}
        )
    ctx = shell_context(request)
    ctx["maps"] = maps
    ctx["active_id"] = None
    return templates.TemplateResponse(request, "index.html", ctx)
