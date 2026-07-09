from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
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


def _clean_disposition(value: str | None) -> str:
    return value if value in DISPOSITIONS else "neutral"


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    ctx = shell_context(request)
    ctx["factions"] = _roster(db, campaign.id)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_form.html", {"faction": None, "dispositions": DISPOSITIONS}
    )


@router.post("", response_class=HTMLResponse)
def create(
    request: Request,
    name: str = Form(...),
    disposition: str = Form("neutral"),
    goals: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    db.add(
        Faction(
            campaign_id=campaign.id,
            name=name.strip(),
            disposition=_clean_disposition(disposition),
            goals=goals.strip() or None,
            description=description.strip() or None,
        )
    )
    db.commit()
    return templates.TemplateResponse(
        request, "_roster.html", {"factions": _roster(db, campaign.id)}
    )


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


@router.get("/{faction_id}/edit", response_class=HTMLResponse)
def edit(
    request: Request,
    faction_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    faction = _owned(db, faction_id, campaign.id)
    return templates.TemplateResponse(
        request, "_form.html", {"faction": faction, "dispositions": DISPOSITIONS}
    )


@router.post("/{faction_id}", response_class=HTMLResponse)
def update(
    request: Request,
    faction_id: int,
    name: str = Form(...),
    disposition: str = Form("neutral"),
    goals: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    faction = _owned(db, faction_id, campaign.id)
    if faction is not None:
        faction.name = name.strip()
        faction.disposition = _clean_disposition(disposition)
        faction.goals = goals.strip() or None
        faction.description = description.strip() or None
        db.commit()
    return templates.TemplateResponse(
        request, "_detail.html", {"faction": faction, "dispositions": DISPOSITIONS}
    )


@router.post("/{faction_id}/delete", response_class=HTMLResponse)
def delete(
    request: Request,
    faction_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    faction = _owned(db, faction_id, campaign.id)
    if faction is not None:
        db.delete(faction)
        db.commit()
    return templates.TemplateResponse(
        request, "_roster.html", {"factions": _roster(db, campaign.id)}
    )
