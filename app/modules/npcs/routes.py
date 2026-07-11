from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.npcs.models import Npc

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/npcs")

UNAFFILIATED = "Unaffiliated"


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


def register_entities(registry) -> None:
    registry.add_entity_provider("npc", npc_entities)
