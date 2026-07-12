from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.maps.models import Map
from app.modules.maps.uploads import store_map_image

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
    return templates.TemplateResponse(
        request, "_map_list.html", {"maps": _maps(db, campaign.id), "active_id": map_id}
    )


@router.get("/{map_id}/state")
def map_state(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> dict:
    m = _owned_map(db, map_id, campaign.id)
    if m is None:
        return {"map": None}
    return _map_dict(m)


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
