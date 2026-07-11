from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core import config
from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.npcs.models import DISPOSITIONS, Npc

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/npcs")

UNAFFILIATED = "Unaffiliated"

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_PORTRAIT_BYTES = 5 * 1024 * 1024


def _store_portrait(upload: UploadFile | None) -> tuple[str | None, str | None]:
    """Validate + persist a portrait. Returns (relative_path, error)."""
    if upload is None or not upload.filename:
        return None, None
    ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return None, "Unsupported image type."
    data = upload.file.read()
    if not data:
        return None, None
    if len(data) > MAX_PORTRAIT_BYTES:
        return None, "Portrait too large (max 5 MB)."
    fname = f"{uuid.uuid4().hex}.{ext}"
    (config.PORTRAITS_DIR / fname).write_bytes(data)
    return f"portraits/{fname}", None


def _delete_portrait_file(rel_path: str | None) -> None:
    if rel_path:
        try:
            (config.MEDIA_DIR / rel_path).unlink(missing_ok=True)
        except OSError:
            pass


def npc_entities(db: Session, campaign_id: int) -> list[tuple[int, str]]:
    """Entity-registry provider so relationships can target NPCs by name."""
    rows = db.query(Npc).filter_by(campaign_id=campaign_id).order_by(Npc.name).all()
    return [(n.id, n.name) for n in rows]


def _grouped_roster(
    db: Session, registry, campaign_id: int, faction_filter: str | None = None
) -> list[tuple[str, list[Npc]]]:
    """NPCs grouped by resolved faction name; null/dangling faction -> Unaffiliated.
    `faction_filter`: None=all, 'none'=Unaffiliated only, '<id>'=that faction only."""
    npcs = db.query(Npc).filter_by(campaign_id=campaign_id).order_by(Npc.name).all()
    fmap = dict(registry.entities("faction", db, campaign_id))  # {faction_id: name}
    groups: dict[str, list[Npc]] = {}
    for n in npcs:
        gname = (fmap.get(n.faction_id) if n.faction_id else None) or UNAFFILIATED
        groups.setdefault(gname, []).append(n)

    if faction_filter == "none":
        groups = {UNAFFILIATED: groups.get(UNAFFILIATED, [])}
    elif faction_filter:
        fid = int(faction_filter) if faction_filter.isdigit() else None
        wanted = fmap.get(fid) if fid is not None else None
        groups = {wanted: groups.get(wanted, [])} if wanted else {}

    ordered = sorted(g for g in groups if g != UNAFFILIATED)
    result = [(g, groups[g]) for g in ordered]
    if UNAFFILIATED in groups:
        result.append((UNAFFILIATED, groups[UNAFFILIATED]))
    return result


def _owned(db: Session, npc_id: int, campaign_id: int) -> Npc | None:
    n = db.get(Npc, npc_id)
    return n if n is not None and n.campaign_id == campaign_id else None


def _clean_disposition(value: str | None) -> str:
    return value if value in DISPOSITIONS else "neutral"


def _clean_faction_id(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def _form_ctx(
    request: Request, db: Session, campaign_id: int, npc: Npc | None, error: str | None = None
) -> dict:
    registry = request.app.state.registry
    return {
        "npc": npc,
        "factions": registry.entities("faction", db, campaign_id),
        "dispositions": DISPOSITIONS,
        "error": error,
        "prefill_name": "",
        "prefill_motivation": "",
        "prefill_voice": "",
    }


def _detail_ctx(request: Request, db: Session, campaign_id: int, npc: Npc | None) -> dict:
    registry = request.app.state.registry
    faction_name = (
        registry.resolve("faction", npc.faction_id, db, campaign_id)
        if npc and npc.faction_id
        else None
    )
    return {"npc": npc, "faction_name": faction_name}


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    faction_id: str | None = None,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    registry = request.app.state.registry
    groups = _grouped_roster(db, registry, campaign.id, faction_id)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "_roster.html", {"groups": groups})
    ctx = shell_context(request)
    ctx["groups"] = groups
    ctx["factions"] = registry.entities("faction", db, campaign.id)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def new(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_form.html", _form_ctx(request, db, campaign.id, None)
    )


@router.post("", response_class=HTMLResponse)
def create(
    request: Request,
    name: str = Form(...),
    disposition: str = Form("neutral"),
    faction_id: str = Form(""),
    statblock: str = Form(""),
    motivation: str = Form(""),
    secrets: str = Form(""),
    voice: str = Form(""),
    portrait: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    portrait_path, error = _store_portrait(portrait)
    if error:
        return templates.TemplateResponse(
            request, "_form.html", _form_ctx(request, db, campaign.id, None, error)
        )
    db.add(
        Npc(
            campaign_id=campaign.id,
            name=name.strip(),
            disposition=_clean_disposition(disposition),
            faction_id=_clean_faction_id(faction_id),
            statblock=statblock.strip() or None,
            motivation=motivation.strip() or None,
            secrets=secrets.strip() or None,
            voice=voice.strip() or None,
            portrait_path=portrait_path,
        )
    )
    db.commit()
    registry = request.app.state.registry
    return templates.TemplateResponse(
        request, "_roster.html", {"groups": _grouped_roster(db, registry, campaign.id)}
    )


@router.get("/{npc_id}", response_class=HTMLResponse)
def detail(
    request: Request,
    npc_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    npc = _owned(db, npc_id, campaign.id)
    return templates.TemplateResponse(
        request, "_detail.html", _detail_ctx(request, db, campaign.id, npc)
    )


@router.get("/{npc_id}/edit", response_class=HTMLResponse)
def edit(
    request: Request,
    npc_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    npc = _owned(db, npc_id, campaign.id)
    return templates.TemplateResponse(
        request, "_form.html", _form_ctx(request, db, campaign.id, npc)
    )


@router.post("/{npc_id}", response_class=HTMLResponse)
def update(
    request: Request,
    npc_id: int,
    name: str = Form(...),
    disposition: str = Form("neutral"),
    faction_id: str = Form(""),
    statblock: str = Form(""),
    motivation: str = Form(""),
    secrets: str = Form(""),
    voice: str = Form(""),
    portrait: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    npc = _owned(db, npc_id, campaign.id)
    if npc is not None:
        portrait_path, error = _store_portrait(portrait)
        if error:
            return templates.TemplateResponse(
                request, "_form.html", _form_ctx(request, db, campaign.id, npc, error)
            )
        if portrait_path:
            _delete_portrait_file(npc.portrait_path)
            npc.portrait_path = portrait_path
        npc.name = name.strip()
        npc.disposition = _clean_disposition(disposition)
        npc.faction_id = _clean_faction_id(faction_id)
        npc.statblock = statblock.strip() or None
        npc.motivation = motivation.strip() or None
        npc.secrets = secrets.strip() or None
        npc.voice = voice.strip() or None
        db.commit()
    return templates.TemplateResponse(
        request, "_detail.html", _detail_ctx(request, db, campaign.id, npc)
    )


@router.post("/{npc_id}/delete", response_class=HTMLResponse)
def delete(
    request: Request,
    npc_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    npc = _owned(db, npc_id, campaign.id)
    if npc is not None:
        _delete_portrait_file(npc.portrait_path)
        db.delete(npc)
        db.commit()
    registry = request.app.state.registry
    return templates.TemplateResponse(
        request, "_roster.html", {"groups": _grouped_roster(db, registry, campaign.id)}
    )


def register_entities(registry) -> None:
    registry.add_entity_provider("npc", npc_entities)
