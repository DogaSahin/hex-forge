from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.core.websocket import manager
from app.modules.maps.fog import reduce_ops
from app.modules.maps.geometry import clamp_hp, snap_to_grid
from app.modules.maps.models import DIAGONAL_RULES, FogRegion, Map, Token
from app.modules.maps.projection import player_state
from app.modules.maps.uploads import store_map_image, store_token_image

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/map")
token_router = APIRouter(prefix="/token")

TOKEN_LAYERS = ("tokens", "dm")


def _maps(db: Session, campaign_id: int) -> list[Map]:
    return db.query(Map).filter_by(campaign_id=campaign_id).order_by(Map.name).all()


def _owned_map(db: Session, map_id: int, campaign_id: int) -> Map | None:
    m = db.get(Map, map_id)
    return m if m is not None and m.campaign_id == campaign_id else None


def _token_dm_dict(t: Token) -> dict:
    return {
        "id": t.id,
        "layer": t.layer,
        "kind": t.kind,
        "x": t.x,
        "y": t.y,
        "size": t.size,
        "color": t.color,
        "image_path": t.image_path,
        "name": t.name,
        "hp_current": t.hp_current,
        "hp_max": t.hp_max,
        "hp_visible_to_players": t.hp_visible_to_players,
        "visible_to_players": t.visible_to_players,
    }


def _owned_token(db: Session, token_id: int, campaign_id: int) -> Token | None:
    t = db.get(Token, token_id)
    if t is None:
        return None
    m = db.get(Map, t.map_id)
    return t if m is not None and m.campaign_id == campaign_id else None


def map_jump(db: Session, campaign_id: int) -> list[dict]:
    return [{"label": m.name, "url": f"/map/{m.id}", "kind": "map"} for m in _maps(db, campaign_id)]


@router.get("/{map_id}", response_class=HTMLResponse)
def editor(
    request: Request,
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    m = _owned_map(db, map_id, campaign.id)
    return _editor_response(request, db, m)


def _editor_response(request: Request, db: Session, m: Map | None) -> HTMLResponse:
    return templates.TemplateResponse(request, "_editor.html", {"map": m})


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


@router.post("", response_class=HTMLResponse)
def create_map(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    if name.strip():
        db.add(Map(campaign_id=campaign.id, name=name.strip()))
        db.commit()
    return templates.TemplateResponse(
        request, "_map_list.html", {"maps": _maps(db, campaign.id), "active_id": None}
    )


@router.post("/{map_id}/delete", response_class=HTMLResponse)
def delete_map(
    request: Request,
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    m = _owned_map(db, map_id, campaign.id)
    if m is not None:
        # Token/FogRegion rows are cleaned here (tables arrive in Tasks 9/20;
        # these deletes are guarded so this works before and after those tables exist).
        _delete_map_children(db, m.id)
        db.delete(m)
        db.commit()
    return templates.TemplateResponse(
        request, "_map_list.html", {"maps": _maps(db, campaign.id), "active_id": None}
    )


def _delete_map_children(db: Session, map_id: int) -> None:
    """Remove tokens + fog for a map. No-ops cleanly until those tables exist."""
    try:
        from app.modules.maps.models import FogRegion, Token

        db.query(Token).filter_by(map_id=map_id).delete(synchronize_session=False)
        db.query(FogRegion).filter_by(map_id=map_id).delete(synchronize_session=False)
    except ImportError:
        pass


@router.post("/{map_id}/image", response_class=HTMLResponse)
def upload_image(
    request: Request,
    map_id: int,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    m = _owned_map(db, map_id, campaign.id)
    if m is not None:
        rel, w, h, error = store_map_image(image)
        if rel and not error:
            m.image_path, m.image_w, m.image_h = rel, w, h
            db.commit()
    return _editor_response(request, db, m)


@router.post("/{map_id}/token", response_class=HTMLResponse)
def create_token(
    request: Request,
    map_id: int,
    name: str = Form(""),
    kind: str = Form("disc"),
    color: str = Form("#888888"),
    size: str = Form("1"),
    layer: str = Form("tokens"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    m = _owned_map(db, map_id, campaign.id)
    if m is not None:
        db.add(
            Token(
                map_id=m.id,
                name=name.strip(),
                kind="image" if kind == "image" else "disc",
                color=color,
                size=max(1, _int_or(size, 1)),
                layer=layer if layer in TOKEN_LAYERS else "tokens",
                x=(m.grid_size_px or 70),
                y=(m.grid_size_px or 70),
            )
        )
        db.commit()
    return _editor_response(request, db, m)


def _int_or(value: str, default: int) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@router.post("/{map_id}/settings", response_class=HTMLResponse)
def update_settings(
    request: Request,
    map_id: int,
    grid_size_px: str = Form("70"),
    grid_offset_x: str = Form("0"),
    grid_offset_y: str = Form("0"),
    grid_visible: str = Form(""),
    feet_per_square: str = Form("5"),
    diagonal_rule: str = Form("chebyshev"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    m = _owned_map(db, map_id, campaign.id)
    if m is not None:
        m.grid_size_px = max(1, _int_or(grid_size_px, 70))
        m.grid_offset_x = _int_or(grid_offset_x, 0)
        m.grid_offset_y = _int_or(grid_offset_y, 0)
        m.grid_visible = bool(grid_visible)
        m.feet_per_square = max(1, _int_or(feet_per_square, 5))
        if diagonal_rule in DIAGONAL_RULES:
            m.diagonal_rule = diagonal_rule
        db.commit()
    return templates.TemplateResponse(request, "_settings.html", {"map": m})


@router.get("/{map_id}/state")
def map_state(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    m = _owned_map(db, map_id, campaign.id)
    if m is None:
        return {"map": None, "tokens": [], "fog": []}
    return {"map": _map_dict(m), "tokens": _tokens_dm(db, m.id), "fog": _fog_ops(db, m.id)}


@router.get("/{map_id}/player-state")
def map_player_state(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    m = _owned_map(db, map_id, campaign.id)
    if m is None:
        return {"map": None, "tokens": [], "fog": []}
    tokens = db.query(Token).filter_by(map_id=m.id).order_by(Token.id).all()
    return player_state(m, tokens, _fog_ops(db, m.id))


def _tokens_dm(db: Session, map_id: int) -> list[dict]:
    rows = db.query(Token).filter_by(map_id=map_id).order_by(Token.id).all()
    return [_token_dm_dict(t) for t in rows]


def _fog_ops(db: Session, map_id: int) -> list[dict]:
    rows = db.query(FogRegion).filter_by(map_id=map_id).order_by(FogRegion.seq, FogRegion.id).all()
    ops = [{"op": r.op, "geom": json.loads(r.geom_json)} for r in rows]
    return reduce_ops(ops)


def _next_fog_seq(db: Session, map_id: int) -> int:
    rows = db.query(FogRegion).filter_by(map_id=map_id).all()
    return max((r.seq for r in rows), default=-1) + 1


@router.post("/{map_id}/fog")
async def add_fog(
    map_id: int,
    op: str = Form("reveal"),
    geom: str = Form("{}"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    m = _owned_map(db, map_id, campaign.id)
    if m is None or op not in ("reveal", "hide"):
        return {"ok": False}
    try:
        parsed = json.loads(geom)
    except ValueError:
        return {"ok": False}
    if not isinstance(parsed, dict):
        return {"ok": False}
    db.add(FogRegion(map_id=m.id, seq=_next_fog_seq(db, m.id), op=op, geom_json=json.dumps(parsed)))
    db.commit()
    await _publish_map_changed(m.id)
    return {"ok": True}


@router.post("/{map_id}/fog/reveal-all")
async def fog_reveal_all(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    m = _owned_map(db, map_id, campaign.id)
    if m is None:
        return {"ok": False}
    db.add(
        FogRegion(
            map_id=m.id,
            seq=_next_fog_seq(db, m.id),
            op="reveal",
            geom_json=json.dumps({"type": "all"}),
        )
    )
    db.commit()
    await _publish_map_changed(m.id)
    return {"ok": True}


@router.post("/{map_id}/fog/hide-all")
async def fog_hide_all(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    m = _owned_map(db, map_id, campaign.id)
    if m is None:
        return {"ok": False}
    db.query(FogRegion).filter_by(map_id=m.id).delete(synchronize_session=False)
    db.commit()
    await _publish_map_changed(m.id)
    return {"ok": True}


def _map_dict(m: Map) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "image_path": m.image_path,
        "image_w": m.image_w,
        "image_h": m.image_h,
        "grid_size_px": m.grid_size_px,
        "grid_offset_x": m.grid_offset_x,
        "grid_offset_y": m.grid_offset_y,
        "grid_visible": m.grid_visible,
        "feet_per_square": m.feet_per_square,
        "diagonal_rule": m.diagonal_rule,
        "is_active": m.is_active,
    }


async def _publish_map_changed(map_id: int) -> None:
    """Coarse "something changed, refetch" signal. Contentless by design so it never
    risks leaking DM-only fields; consumers refetch via the existing /state endpoints,
    which already apply the two-surface split. Full topic gating lands in Task 29."""
    await manager.publish(f"map:{map_id}", {"action": "map_changed", "map_id": map_id})


async def _publish_token_move(t: Token) -> None:
    """Publish a positional delta. Topic gating (player-safe vs dm) lands in Task 28;
    for now publish on the player-safe topic."""
    await manager.publish(
        f"map:{t.map_id}",
        {"action": "token.move", "map_id": t.map_id, "token_id": t.id, "x": t.x, "y": t.y},
    )


@token_router.post("/{token_id}/move")
async def move_token(
    token_id: int,
    x: str = Form("0"),
    y: str = Form("0"),
    snap: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    t = _owned_token(db, token_id, campaign.id)
    if t is None:
        return {"ok": False}
    t.x = _int_or(x, t.x)
    t.y = _int_or(y, t.y)
    if snap:
        m = db.get(Map, t.map_id)
        if m is not None:
            t.x, t.y = snap_to_grid(t.x, t.y, m.grid_size_px, m.grid_offset_x, m.grid_offset_y)
    db.commit()
    await _publish_token_move(t)
    return {"ok": True}


@token_router.post("/{token_id}/image", response_class=HTMLResponse)
def upload_token_image(
    request: Request,
    token_id: int,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    t = _owned_token(db, token_id, campaign.id)
    if t is not None:
        rel, _w, _h, error = store_token_image(image)
        if rel and not error:
            t.image_path, t.kind = rel, "image"
            db.commit()
    m = db.get(Map, t.map_id) if t is not None else None
    return _editor_response(request, db, m)


@token_router.post("/{token_id}", response_class=HTMLResponse)
async def edit_token(
    request: Request,
    token_id: int,
    name: str = Form(None),
    size: str = Form(None),
    color: str = Form(None),
    layer: str = Form(None),
    visible_to_players: str = Form(None),
    hp_current: str = Form(None),
    hp_max: str = Form(None),
    hp_visible_to_players: str = Form(None),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    t = _owned_token(db, token_id, campaign.id)
    m = db.get(Map, t.map_id) if t is not None else None
    if t is not None:
        if name is not None:
            t.name = name.strip()
        if size is not None:
            t.size = max(1, _int_or(size, t.size))
        if color is not None:
            t.color = color
        if layer is not None and layer in TOKEN_LAYERS:
            t.layer = layer
        if visible_to_players is not None:
            t.visible_to_players = bool(visible_to_players)
        # hp_max must be applied before hp_current so clamp_hp uses the new max.
        if hp_max is not None:
            t.hp_max = _int_or_none(hp_max)
        if hp_current is not None:
            t.hp_current = clamp_hp(_int_or(hp_current, 0), t.hp_max)
        if hp_visible_to_players is not None:
            t.hp_visible_to_players = bool(hp_visible_to_players)
        db.commit()
        await _publish_map_changed(t.map_id)
    return _editor_response(request, db, m)


@token_router.post("/{token_id}/delete", response_class=HTMLResponse)
async def delete_token(
    request: Request,
    token_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    t = _owned_token(db, token_id, campaign.id)
    m = db.get(Map, t.map_id) if t is not None else None
    if t is not None:
        map_id = t.map_id
        db.delete(t)
        db.commit()
        await _publish_map_changed(map_id)
    return _editor_response(request, db, m)


@token_router.get("/{token_id}/menu", response_class=HTMLResponse)
def token_menu(
    request: Request,
    token_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    t = _owned_token(db, token_id, campaign.id)
    return templates.TemplateResponse(request, "_token_menu.html", {"t": t})
