from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.dice import parser
from app.modules.dice.models import RollHistory, SavedRoll

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/dice")

HISTORY_LIMIT = 50


def _saved(db: Session, campaign_id: int) -> list[SavedRoll]:
    return db.query(SavedRoll).filter_by(campaign_id=campaign_id).order_by(SavedRoll.label).all()


def _history(db: Session, campaign_id: int) -> list[RollHistory]:
    return (
        db.query(RollHistory)
        .filter_by(campaign_id=campaign_id)
        .order_by(RollHistory.rolled_at.desc(), RollHistory.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    ctx = shell_context(request)
    ctx["saved_rolls"] = _saved(db, campaign.id)
    ctx["history"] = _history(db, campaign.id)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.post("/roll", response_class=HTMLResponse)
def roll(
    request: Request,
    expression: str = Form(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    try:
        result = parser.evaluate(expression)
    except parser.DiceError as exc:
        return templates.TemplateResponse(
            request, "_result.html", {"error": str(exc), "expression": expression}
        )
    db.add(
        RollHistory(
            campaign_id=campaign.id,
            expression=expression,
            result=result.total,
            breakdown_json=json.dumps(asdict(result)),
        )
    )
    db.commit()
    resp = templates.TemplateResponse(
        request, "_result.html", {"result": result, "expression": expression}
    )
    resp.headers["HX-Trigger"] = "roll-logged"
    return resp


@router.get("/history", response_class=HTMLResponse)
def history(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_history.html", {"history": _history(db, campaign.id)}
    )


@router.post("/saved", response_class=HTMLResponse)
def create_saved(
    request: Request,
    label: str = Form(...),
    expression: str = Form(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    db.add(SavedRoll(campaign_id=campaign.id, label=label.strip(), expression=expression.strip()))
    db.commit()
    return templates.TemplateResponse(
        request, "_saved_rolls.html", {"saved_rolls": _saved(db, campaign.id)}
    )


@router.post("/saved/{saved_id}/delete", response_class=HTMLResponse)
def delete_saved(
    request: Request,
    saved_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    obj = db.get(SavedRoll, saved_id)
    if obj is not None and obj.campaign_id == campaign.id:
        db.delete(obj)
        db.commit()
    return templates.TemplateResponse(
        request, "_saved_rolls.html", {"saved_rolls": _saved(db, campaign.id)}
    )
