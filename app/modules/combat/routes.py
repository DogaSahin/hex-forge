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
from app.modules.combat.projection import hp_band
from app.modules.combat.statblock import parse_stats

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


def _tracker_ctx(request: Request, db: Session, encounter: Encounter | None) -> dict:
    campaign_id = encounter.campaign_id if encounter is not None else None
    npc_options = (
        request.app.state.registry.entities("npc", db, campaign_id)
        if campaign_id is not None
        else []
    )
    if encounter is None:
        return {
            "encounter": None,
            "rows": [],
            "conditions_all": CONDITIONS,
            "npc_options": npc_options,
            "prefill": None,
        }
    rows = _combatants(db, encounter.id)
    for c in rows:
        c.cond_list = _conditions(c)  # transient attr for the template; not persisted
        c.band = hp_band(c.hp_current, c.hp_max)  # shared band (single source of truth)
    return {
        "encounter": encounter,
        "rows": rows,
        "conditions_all": CONDITIONS,
        "npc_options": npc_options,
        "prefill": None,
    }


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
    ctx.update(_tracker_ctx(request, db, None))
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
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


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


def _next_sort_order(db: Session, encounter_id: int) -> int:
    rows = _combatants(db, encounter_id)
    return (max((c.sort_order for c in rows), default=0) + 1) if rows else 0


def _int_or(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@router.post("/{encounter_id}/combatant", response_class=HTMLResponse)
async def add_combatant(
    request: Request,
    encounter_id: int,
    name: str = Form(...),
    initiative: str = Form("0"),
    hp_max: str = Form("0"),
    hp_current: str = Form(""),
    ac: str = Form(""),
    is_pc: str = Form(""),
    npc_id: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    if enc is not None and name.strip():
        hp_m = _int_or(hp_max, 0)
        hp_c = _int_or(hp_current, hp_m) if hp_current.strip() else hp_m
        db.add(
            Combatant(
                encounter_id=enc.id,
                name=name.strip(),
                initiative=_int_or(initiative, 0),
                hp_max=hp_m,
                hp_current=max(0, min(hp_c, hp_m)) if hp_m else max(0, hp_c),
                ac=_int_or_none(ac),
                is_pc=bool(is_pc),
                npc_id=_int_or_none(npc_id),
                sort_order=_next_sort_order(db, enc.id),
            )
        )
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


@router.post("/combatant/{combatant_id}/delete", response_class=HTMLResponse)
async def delete_combatant(
    request: Request,
    combatant_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    c = _owned_combatant(db, combatant_id, campaign.id)
    if c is None:
        return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, None))
    enc = db.get(Encounter, c.encounter_id)
    if enc.active_combatant_id == c.id:
        ordered = [x.id for x in _combatants(db, enc.id)]
        if len(ordered) <= 1:
            enc.active_combatant_id = None
        else:
            i = ordered.index(c.id)
            enc.active_combatant_id = ordered[(i + 1) % len(ordered)]
    db.delete(c)
    db.commit()
    await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


def _npc_options(request: Request, db: Session, campaign_id: int) -> list[tuple[int, str]]:
    return request.app.state.registry.entities("npc", db, campaign_id)


@router.get("/{encounter_id}/add-npc", response_class=HTMLResponse)
def add_npc_form(
    request: Request,
    encounter_id: int,
    npc_id: str = "",
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    ctx = {
        "encounter": enc,
        "npc_options": _npc_options(request, db, campaign.id),
        "prefill": {"name": "", "hp_max": "", "hp_current": "", "ac": "", "npc_id": ""},
    }
    nid = _int_or_none(npc_id)
    if enc is not None and nid is not None:
        detail = request.app.state.registry.entity_detail("npc", nid, db, campaign.id)
        if detail is not None:
            stats = parse_stats(detail.get("statblock"))
            ctx["prefill"] = {
                "name": detail["name"],
                "hp_max": stats.get("hp_max", ""),
                "hp_current": stats.get("hp_current", ""),
                "ac": stats.get("ac", ""),
                "npc_id": str(nid),
            }
    return templates.TemplateResponse(request, "_combatant_form.html", ctx)


@router.post("/{encounter_id}/sort", response_class=HTMLResponse)
async def sort_by_initiative(
    request: Request,
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    if enc is not None:
        rows = sorted(_combatants(db, enc.id), key=lambda c: (-c.initiative, c.id))
        for i, c in enumerate(rows):
            c.sort_order = i
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


@router.post("/{encounter_id}/reorder", response_class=HTMLResponse)
async def reorder(
    request: Request,
    encounter_id: int,
    order: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    if enc is not None:
        ids = [int(x) for x in order.split(",") if x.strip().isdigit()]
        rank = {cid: i for i, cid in enumerate(ids)}
        for c in _combatants(db, enc.id):
            if c.id in rank:
                c.sort_order = rank[c.id]
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


def _clamp_hp(current: int, hp_max: int) -> int:
    if hp_max <= 0:
        return max(0, current)
    return max(0, min(current, hp_max))


@router.post("/combatant/{combatant_id}/damage", response_class=HTMLResponse)
async def damage(
    request: Request,
    combatant_id: int,
    amount: str = Form("0"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return await _apply_hp(request, combatant_id, -_int_or(amount, 0), db, campaign)


@router.post("/combatant/{combatant_id}/heal", response_class=HTMLResponse)
async def heal(
    request: Request,
    combatant_id: int,
    amount: str = Form("0"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return await _apply_hp(request, combatant_id, _int_or(amount, 0), db, campaign)


async def _apply_hp(request, combatant_id, delta, db, campaign) -> HTMLResponse:
    c = _owned_combatant(db, combatant_id, campaign.id)
    enc = db.get(Encounter, c.encounter_id) if c is not None else None
    if c is not None:
        c.hp_current = _clamp_hp(c.hp_current + delta, c.hp_max)
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


@router.post("/combatant/{combatant_id}/ac", response_class=HTMLResponse)
async def edit_ac(
    request: Request,
    combatant_id: int,
    ac: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    c = _owned_combatant(db, combatant_id, campaign.id)
    enc = db.get(Encounter, c.encounter_id) if c is not None else None
    if c is not None:
        c.ac = _int_or_none(ac)
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


def _set_conditions(c: Combatant, names: list[str]) -> None:
    c.conditions_json = json.dumps(names)


@router.post("/combatant/{combatant_id}/condition", response_class=HTMLResponse)
async def edit_condition(
    request: Request,
    combatant_id: int,
    name: str = Form(""),
    op: str = Form("add"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    c = _owned_combatant(db, combatant_id, campaign.id)
    enc = db.get(Encounter, c.encounter_id) if c is not None else None
    label = name.strip()
    if c is not None and label:
        current = _conditions(c)
        if op == "remove":
            current = [x for x in current if x != label]
        elif label not in current:
            current.append(label)
        _set_conditions(c, current)
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


@router.post("/combatant/{combatant_id}/concentration", response_class=HTMLResponse)
async def toggle_concentration(
    request: Request,
    combatant_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    c = _owned_combatant(db, combatant_id, campaign.id)
    enc = db.get(Encounter, c.encounter_id) if c is not None else None
    if c is not None:
        c.concentration = not c.concentration
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))


def advance_turn(
    active_id: int | None, ordered_ids: list[int], current_round: int
) -> tuple[int | None, int]:
    """Next-turn engine. None/stale active -> first (round unchanged, starts combat);
    wrapping past the last -> first + round++. Empty -> (None, round)."""
    if not ordered_ids:
        return None, current_round
    if active_id not in ordered_ids:
        return ordered_ids[0], current_round
    idx = ordered_ids.index(active_id)
    if idx + 1 < len(ordered_ids):
        return ordered_ids[idx + 1], current_round
    return ordered_ids[0], current_round + 1


@router.post("/{encounter_id}/next-turn", response_class=HTMLResponse)
async def next_turn(
    request: Request,
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    enc = _owned_encounter(db, encounter_id, campaign.id)
    if enc is not None:
        ordered = [c.id for c in _combatants(db, enc.id)]
        enc.active_combatant_id, enc.round = advance_turn(
            enc.active_combatant_id, ordered, enc.round
        )
        db.commit()
        await _notify(enc.id)
    return templates.TemplateResponse(request, "_tracker.html", _tracker_ctx(request, db, enc))
