from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.factions.models import DISPOSITIONS, Faction, FactionClock

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/factions")

CLOCK_MIN_SEGMENTS = 2
CLOCK_MAX_SEGMENTS = 12


def _roster(db: Session, campaign_id: int) -> list[Faction]:
    return db.query(Faction).filter_by(campaign_id=campaign_id).order_by(Faction.name).all()


def _owned(db: Session, faction_id: int, campaign_id: int) -> Faction | None:
    f = db.get(Faction, faction_id)
    return f if f is not None and f.campaign_id == campaign_id else None


def _owned_clock(db: Session, clock_id: int, campaign_id: int) -> FactionClock | None:
    clock = db.get(FactionClock, clock_id)
    if clock is None or clock.faction.campaign_id != campaign_id:
        return None
    return clock


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


@router.post("/{faction_id}/clocks", response_class=HTMLResponse)
def create_clock(
    request: Request,
    faction_id: int,
    name: str = Form(...),
    segments: int = Form(6),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    faction = _owned(db, faction_id, campaign.id)
    if faction is not None:
        seg = max(CLOCK_MIN_SEGMENTS, min(int(segments), CLOCK_MAX_SEGMENTS))
        faction.clocks.append(FactionClock(name=name.strip(), segments=seg, filled=0))
        db.commit()
    return templates.TemplateResponse(request, "_clocks.html", {"faction": faction})


@router.post("/clocks/{clock_id}/delete", response_class=HTMLResponse)
def delete_clock(
    request: Request,
    clock_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    clock = _owned_clock(db, clock_id, campaign.id)
    faction = clock.faction if clock is not None else None
    if clock is not None:
        db.delete(clock)
        db.commit()
    return templates.TemplateResponse(request, "_clocks.html", {"faction": faction})


@router.post("/clocks/{clock_id}/fill", response_class=HTMLResponse)
def fill_clock(
    request: Request,
    clock_id: int,
    segment: int = Form(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    clock = _owned_clock(db, clock_id, campaign.id)
    if clock is None:
        return HTMLResponse("")  # not owned by the active campaign — no-op, no mutation
    target = segment + 1  # clicking 0-based index i fills 1..i+1
    # Clicking the current top segment toggles it off.
    new_filled = segment if clock.filled == target else target
    clock.filled = max(0, min(new_filled, clock.segments))
    db.commit()
    return templates.TemplateResponse(request, "_clock.html", {"clock": clock})
