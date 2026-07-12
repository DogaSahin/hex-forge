from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.core.websocket import manager
from app.modules.combat.models import CONDITIONS, Combatant, Encounter
from app.modules.combat.statblock import parse_stats  # noqa: F401

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/combat")


async def _notify(encounter_id: int) -> None:
    """Publish the contentless live-sync signal. No combatant state travels — the
    two-surface boundary is enforced at the fetch endpoint, not the message."""
    await manager.publish(
        f"combat:{encounter_id}",
        {"action": "combat_changed", "encounter_id": encounter_id},
    )


def _encounters(db: Session, campaign_id: int) -> list[Encounter]:
    return db.query(Encounter).filter_by(campaign_id=campaign_id).order_by(Encounter.name).all()


def _owned_encounter(db: Session, encounter_id: int, campaign_id: int) -> Encounter | None:
    e = db.get(Encounter, encounter_id)
    return e if e is not None and e.campaign_id == campaign_id else None


def _owned_combatant(db: Session, combatant_id: int, campaign_id: int) -> Combatant | None:
    c = db.get(Combatant, combatant_id)
    if c is None:
        return None
    e = db.get(Encounter, c.encounter_id)
    return c if e is not None and e.campaign_id == campaign_id else None


def _combatants(db: Session, encounter_id: int) -> list[Combatant]:
    return (
        db.query(Combatant)
        .filter_by(encounter_id=encounter_id)
        .order_by(Combatant.sort_order, Combatant.id)
        .all()
    )


def _conditions(c: Combatant) -> list[str]:
    try:
        v = json.loads(c.conditions_json)
        return [str(x) for x in v] if isinstance(v, list) else []
    except (ValueError, TypeError):
        return []


def _tracker_ctx(db: Session, encounter: Encounter | None) -> dict:
    if encounter is None:
        return {"encounter": None, "rows": [], "conditions_all": CONDITIONS}
    rows = _combatants(db, encounter.id)
    for c in rows:
        c.cond_list = _conditions(c)  # transient attr for the template; not persisted
    return {"encounter": encounter, "rows": rows, "conditions_all": CONDITIONS}


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    encounters = _encounters(db, campaign.id)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request, "_encounter_list.html", {"encounters": encounters, "active_id": None}
        )
    ctx = shell_context(request)
    ctx["encounters"] = encounters
    ctx["active_id"] = None
    ctx.update(_tracker_ctx(db, None))
    return templates.TemplateResponse(request, "index.html", ctx)


def encounter_jump(db: Session, campaign_id: int) -> list[dict]:
    rows = _encounters(db, campaign_id)
    return [{"label": e.name, "url": f"/combat/{e.id}", "kind": "encounter"} for e in rows]


@router.post("", response_class=HTMLResponse)
def create_encounter(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    if name.strip():
        db.add(Encounter(campaign_id=campaign.id, name=name.strip()))
        db.commit()
    return templates.TemplateResponse(
        request,
        "_encounter_list.html",
        {"encounters": _encounters(db, campaign.id), "active_id": None},
    )


@router.get("/{encounter_id}", response_class=HTMLResponse)
def tracker(
    request: Request,
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(db, enc))


@router.post("/{encounter_id}/delete", response_class=HTMLResponse)
def delete_encounter(
    request: Request,
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    if enc is not None:
        db.query(Combatant).filter_by(encounter_id=enc.id).delete(synchronize_session=False)
        db.delete(enc)
        db.commit()
    return templates.TemplateResponse(
        request,
        "_encounter_list.html",
        {"encounters": _encounters(db, campaign.id), "active_id": None},
    )


@router.post("/{encounter_id}/set-active", response_class=HTMLResponse)
def set_active(
    request: Request,
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    if enc is not None:
        db.query(Encounter).filter_by(campaign_id=campaign.id).update(
            {Encounter.is_active: False}, synchronize_session=False
        )
        enc.is_active = True
        db.commit()
    return templates.TemplateResponse(
        request,
        "_encounter_list.html",
        {"encounters": _encounters(db, campaign.id), "active_id": encounter_id},
    )
