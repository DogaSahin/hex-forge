from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.wiki.links import render_markdown, slugify
from app.modules.wiki.models import Tag, WikiPage, WikiPageTag

MODULE_DIR = Path(__file__).resolve().parent
templates = module_templates(MODULE_DIR)

router = APIRouter(prefix="/wiki")


def _pages(
    db: Session, campaign_id: int, category: str | None = None, tag: str | None = None
) -> list[WikiPage]:
    q = db.query(WikiPage).filter_by(campaign_id=campaign_id)
    if category:
        q = q.filter(WikiPage.category == category)
    if tag:
        q = (
            q.join(WikiPageTag, WikiPageTag.page_id == WikiPage.id)
            .join(Tag, Tag.id == WikiPageTag.tag_id)
            .filter(Tag.campaign_id == campaign_id, Tag.name == tag)
        )
    return q.order_by(WikiPage.title).all()


def _owned_by_slug(db: Session, slug: str, campaign_id: int) -> WikiPage | None:
    return db.query(WikiPage).filter_by(campaign_id=campaign_id, slug=slug).first()


def _categories(db: Session, campaign_id: int) -> list[str]:
    rows = (
        db.query(WikiPage.category)
        .filter(WikiPage.campaign_id == campaign_id, WikiPage.category.isnot(None))
        .distinct()
        .all()
    )
    return sorted({r[0] for r in rows if r[0]})


def _all_tags(db: Session, campaign_id: int) -> list[Tag]:
    return db.query(Tag).filter_by(campaign_id=campaign_id).order_by(Tag.name).all()


def _unique_slug(db: Session, campaign_id: int, title: str, exclude_id: int | None = None) -> str:
    base = slugify(title)
    slug = base
    n = 2
    while True:
        row = db.query(WikiPage).filter_by(campaign_id=campaign_id, slug=slug).first()
        if row is None or row.id == exclude_id:
            return slug
        slug = f"{base}-{n}"
        n += 1


def _plain_resolver(name: str) -> tuple[str, bool]:
    # Task 5 replaces this with real page/NPC/faction resolution.
    from urllib.parse import quote

    return (f"/wiki/new?title={quote(name)}", False)


def _detail_ctx(request: Request, db: Session, campaign_id: int, page: WikiPage | None) -> dict:
    if page is None:
        return {"page": None}
    return {
        "page": page,
        "body_html": render_markdown(page.body_md, _plain_resolver),
    }


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    category: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    pages = _pages(db, campaign.id, category, tag)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "_list.html", {"pages": pages})
    ctx = shell_context(request)
    ctx["pages"] = pages
    ctx["categories"] = _categories(db, campaign.id)
    ctx["tags"] = _all_tags(db, campaign.id)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def new(request: Request, title: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_form.html", {"page": None, "prefill_title": title, "error": None}
    )


@router.post("", response_class=HTMLResponse)
def create(
    request: Request,
    title: str = Form(...),
    category: str = Form(""),
    body_md: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    if not title.strip():
        return templates.TemplateResponse(
            request,
            "_form.html",
            {"page": None, "prefill_title": "", "error": "Title is required."},
        )
    page = WikiPage(
        campaign_id=campaign.id,
        title=title.strip(),
        slug=_unique_slug(db, campaign.id, title),
        body_md=body_md.strip() or None,
        category=category.strip() or None,
        updated_at=datetime.now(UTC),
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return templates.TemplateResponse(
        request, "_detail.html", _detail_ctx(request, db, campaign.id, page)
    )


@router.get("/{slug}", response_class=HTMLResponse)
def detail(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    page = _owned_by_slug(db, slug, campaign.id)
    if request.headers.get("HX-Request") or page is None:
        return templates.TemplateResponse(
            request, "_detail.html", _detail_ctx(request, db, campaign.id, page)
        )
    ctx = shell_context(request)
    ctx.update(_detail_ctx(request, db, campaign.id, page))
    ctx["pages"] = _pages(db, campaign.id)
    ctx["categories"] = _categories(db, campaign.id)
    ctx["tags"] = _all_tags(db, campaign.id)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/{slug}/edit", response_class=HTMLResponse)
def edit(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    page = _owned_by_slug(db, slug, campaign.id)
    return templates.TemplateResponse(
        request, "_form.html", {"page": page, "prefill_title": "", "error": None}
    )


@router.post("/{slug}", response_class=HTMLResponse)
def update(
    request: Request,
    slug: str,
    title: str = Form(...),
    category: str = Form(""),
    body_md: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    page = _owned_by_slug(db, slug, campaign.id)
    if page is not None:
        if not title.strip():
            return templates.TemplateResponse(
                request,
                "_form.html",
                {"page": page, "prefill_title": "", "error": "Title is required."},
            )
        page.title = title.strip()
        page.category = category.strip() or None
        page.body_md = body_md.strip() or None
        page.updated_at = datetime.now(UTC)
        # Slug is intentionally NOT regenerated (keeps inbound [[links]] + URLs stable).
        db.commit()
        db.refresh(page)
    return templates.TemplateResponse(
        request, "_detail.html", _detail_ctx(request, db, campaign.id, page)
    )


@router.post("/{slug}/delete", response_class=HTMLResponse)
def delete(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    page = _owned_by_slug(db, slug, campaign.id)
    if page is not None:
        from app.modules.wiki.models import WikiLink

        db.query(WikiLink).filter_by(source_page_id=page.id).delete(synchronize_session=False)
        db.query(WikiPageTag).filter_by(page_id=page.id).delete(synchronize_session=False)
        db.delete(page)
        db.commit()
    return templates.TemplateResponse(request, "_list.html", {"pages": _pages(db, campaign.id)})
