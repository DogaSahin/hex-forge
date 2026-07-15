from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.sessions import services
from app.modules.sessions.models import GameSession

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/sessions")


def _parse_date(raw: str) -> date_type:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date_type.today()


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    ctx = shell_context(request)
    ctx["sessions"] = services.roster(db, campaign.id)
    ctx["session"] = None
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "_form.html", {"session": None})


@router.post("", response_class=HTMLResponse)
def create(
    request: Request,
    title: str = Form(...),
    date: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    clean_title = title.strip()
    if clean_title:
        db.add(
            GameSession(
                campaign_id=campaign.id,
                number=services.next_number(db, campaign.id),
                date=_parse_date(date),
                title=clean_title,
            )
        )
        db.commit()
    return templates.TemplateResponse(
        request, "_list.html", {"sessions": services.roster(db, campaign.id)}
    )


@router.get("/{session_id}", response_class=HTMLResponse)
def detail(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_detail.html", {"session": services.owned(db, session_id, campaign.id)}
    )


@router.get("/{session_id}/edit", response_class=HTMLResponse)
def edit(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_form.html", {"session": services.owned(db, session_id, campaign.id)}
    )


@router.post("/{session_id}", response_class=HTMLResponse)
def update(
    request: Request,
    session_id: int,
    title: str = Form(...),
    date: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    if row is not None and title.strip():
        row.title = title.strip()
        row.date = _parse_date(date)
        db.commit()
    return templates.TemplateResponse(request, "_detail.html", {"session": row})


@router.post("/{session_id}/delete", response_class=HTMLResponse)
def delete(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    if row is not None:
        db.delete(row)
        db.commit()
    return templates.TemplateResponse(
        request, "_list.html", {"sessions": services.roster(db, campaign.id)}
    )


@router.post("/{session_id}/activate", response_class=HTMLResponse)
def activate(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    if row is not None:
        services.activate(db, row)
    return templates.TemplateResponse(request, "_detail.html", {"session": row})
