from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.sessions import services
from app.modules.sessions.models import DEFAULT_TAG, TAGS, GameSession, SessionLog
from app.modules.sessions.recap import TAG_HEADINGS, compile_recap

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/sessions")


def _parse_date(raw: str) -> date_type:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date_type.today()


def _clean_tag(value: str | None) -> str:
    return value if value in TAGS else DEFAULT_TAG


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
        request,
        "_detail.html",
        {
            "session": services.owned(db, session_id, campaign.id),
            "headings": TAG_HEADINGS,
            "recap": "",
        },
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
    return templates.TemplateResponse(
        request, "_detail.html", {"session": row, "headings": TAG_HEADINGS, "recap": ""}
    )


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
    return templates.TemplateResponse(
        request, "_detail.html", {"session": row, "headings": TAG_HEADINGS, "recap": ""}
    )


def _feed(request: Request, session_row: GameSession | None) -> HTMLResponse:
    return templates.TemplateResponse(request, "_log_feed.html", {"session": session_row})


@router.post("/{session_id}/log", response_class=HTMLResponse)
def append_log(
    request: Request,
    session_id: int,
    text: str = Form(...),
    tag: str = Form(DEFAULT_TAG),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    if row is not None and text.strip():
        row.logs.append(SessionLog(text=text.strip(), tag=_clean_tag(tag)))
        db.commit()
        db.refresh(row)
    return _feed(request, row)


@router.post("/{session_id}/summary", response_class=HTMLResponse)
def edit_summary(
    request: Request,
    session_id: int,
    summary: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    if row is not None:
        row.summary = summary.strip() or None
        db.commit()
    return templates.TemplateResponse(request, "_summary.html", {"session": row})


@router.post("/{session_id}/recap", response_class=HTMLResponse)
def compile_session_recap(
    request: Request,
    session_id: int,
    tags: list[str] = Form(default=[]),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    text = compile_recap(row.logs, set(tags)) if row is not None else ""
    return templates.TemplateResponse(
        request, "_recap.html", {"session": row, "recap": text, "headings": TAG_HEADINGS}
    )


@router.post("/{session_id}/recap/apply", response_class=HTMLResponse)
def apply_recap(
    request: Request,
    session_id: int,
    recap: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    row = services.owned(db, session_id, campaign.id)
    if row is not None and recap.strip():
        row.summary = recap.strip()
        db.commit()
    return templates.TemplateResponse(request, "_summary.html", {"session": row})


@router.post("/log/{log_id}/delete", response_class=HTMLResponse)
def delete_log(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    log = services.owned_log(db, log_id, campaign.id)
    row = log.session if log is not None else None
    if log is not None:
        db.delete(log)
        db.commit()
        if row is not None:
            db.refresh(row)
    return _feed(request, row)


@router.post("/log/{log_id}/resolve", response_class=HTMLResponse)
def resolve_thread(
    request: Request,
    log_id: int,
    view: str = Form("feed"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return _set_resolved(request, log_id, datetime.now(UTC), view, db, campaign)


@router.post("/log/{log_id}/unresolve", response_class=HTMLResponse)
def unresolve_thread(
    request: Request,
    log_id: int,
    view: str = Form("feed"),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    return _set_resolved(request, log_id, None, view, db, campaign)


def _threads_card_fragment(request: Request, db: Session, campaign_id: int) -> HTMLResponse:
    # Deferred import: app.modules.sessions.dashboard doesn't exist until Task 7.
    # A module-level import here would break the whole `sessions` module today.
    # Task 7 hoists this to a top-of-file import once dashboard.py lands.
    from app.modules.sessions import dashboard  # noqa: PLC0415

    return HTMLResponse(dashboard.render_threads_card(db, campaign_id))


def _set_resolved(
    request: Request,
    log_id: int,
    value: datetime | None,
    view: str,
    db: Session,
    campaign: Campaign,
) -> HTMLResponse:
    log = services.owned_log(db, log_id, campaign.id)
    row = log.session if log is not None else None
    if log is not None:
        log.resolved_at = value
        db.commit()
        if row is not None:
            db.refresh(row)
    if view == "card":
        # Fired from the dashboard's open-threads card, which needs its own
        # fragment back rather than the session page's feed. Wired up in Task 7.
        return _threads_card_fragment(request, db, campaign.id)
    return _feed(request, row)
