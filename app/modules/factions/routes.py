from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.factions.models import DISPOSITIONS, Faction

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/factions")


def _roster(db: Session, campaign_id: int) -> list[Faction]:
    return db.query(Faction).filter_by(campaign_id=campaign_id).order_by(Faction.name).all()


def _owned(db: Session, faction_id: int, campaign_id: int) -> Faction | None:
    f = db.get(Faction, faction_id)
    return f if f is not None and f.campaign_id == campaign_id else None


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    ctx = shell_context(request)
    ctx["factions"] = _roster(db, campaign.id)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/{faction_id}", response_class=HTMLResponse)
def detail(
    request: Request,
    faction_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    faction = _owned(db, faction_id, campaign.id)
    return templates.TemplateResponse(
        request, "_detail.html", {"faction": faction, "dispositions": DISPOSITIONS}
    )
