from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core import broadcast
from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates

SURFACE_DIR = Path(__file__).resolve().parent
templates = module_templates(SURFACE_DIR)

router = APIRouter(prefix="/player")


@router.get("", response_class=HTMLResponse)
def player_screen(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "player.html", {})


@router.get("/state")
def player_state(
    db: Session = Depends(get_db),
    campaign: Campaign | None = Depends(get_active_campaign),
) -> dict:
    if campaign is None:  # empty DB / no campaign — nothing to show
        return {"active_encounter_id": None, "active_map_id": None}
    return broadcast.snapshot(db, campaign.id)
