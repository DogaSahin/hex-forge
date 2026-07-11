from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
from app.modules.wiki.links import extract_wikilinks, render_markdown, slugify
from app.modules.wiki.models import Tag, WikiLink, WikiPage, WikiPageTag

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


def _page_tags(db: Session, page_id: int) -> list[Tag]:
    return (
        db.query(Tag)
        .join(WikiPageTag, WikiPageTag.tag_id == Tag.id)
        .filter(WikiPageTag.page_id == page_id)
        .order_by(Tag.name)
        .all()
    )


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


class _Resolver:
    """Resolve a [[Name]] against pages -> NPCs -> factions for one campaign.
    Built once per request; used for both link persistence and rendering."""

    def __init__(self, db: Session, registry, campaign_id: int) -> None:
        self._pages = {
            p.title.lower(): (p.id, p.slug)
            for p in db.query(WikiPage).filter_by(campaign_id=campaign_id).all()
        }
        self._npcs = {name.lower(): eid for eid, name in registry.entities("npc", db, campaign_id)}
        self._factions = {
            name.lower(): eid for eid, name in registry.entities("faction", db, campaign_id)
        }

    def ref(self, name: str) -> tuple[str, int | None]:
        key = name.lower()
        if key in self._pages:
            return ("page", self._pages[key][0])
        if key in self._npcs:
            return ("npc", self._npcs[key])
        if key in self._factions:
            return ("faction", self._factions[key])
        return ("page", None)  # unresolved -> page-create target

    def href(self, name: str) -> tuple[str, bool]:
        key = name.lower()
        if key in self._pages:
            return (f"/wiki/{self._pages[key][1]}", True)
        if key in self._npcs:
            return (f"/npcs/{self._npcs[key]}", True)
        if key in self._factions:
            return (f"/factions/{self._factions[key]}", True)
        return (f"/wiki/new?title={quote(name)}", False)


def _rebuild_links(db: Session, registry, page: WikiPage) -> None:
    db.query(WikiLink).filter_by(source_page_id=page.id).delete(synchronize_session=False)
    resolver = _Resolver(db, registry, page.campaign_id)
    for name in extract_wikilinks(page.body_md):
        target_type, target_id = resolver.ref(name)
        db.add(
            WikiLink(
                source_page_id=page.id,
                target_type=target_type,
                target_id=target_id,
                target_title=name,
            )
        )


def _backlinks(db: Session, page: WikiPage) -> list[WikiPage]:
    rows = db.query(WikiLink).filter_by(target_type="page", target_id=page.id).all()
    source_ids = {r.source_page_id for r in rows}
    if not source_ids:
        return []
    return db.query(WikiPage).filter(WikiPage.id.in_(source_ids)).order_by(WikiPage.title).all()


def _detail_ctx(request: Request, db: Session, campaign_id: int, page: WikiPage | None) -> dict:
    if page is None:
        return {"page": None}
    registry = request.app.state.registry
    resolver = _Resolver(db, registry, campaign_id)
    return {
        "page": page,
        "body_html": render_markdown(page.body_md, resolver.href),
        "backlinks": _backlinks(db, page),
        "tags": _page_tags(db, page.id),
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


@router.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    needle = q.strip()
    results: list[WikiPage] = []
    if needle:
        like = f"%{needle}%"
        results = (
            db.query(WikiPage)
            .filter(
                WikiPage.campaign_id == campaign.id,
                (WikiPage.title.ilike(like)) | (WikiPage.body_md.ilike(like)),
            )
            .order_by(WikiPage.title)
            .all()
        )
    return templates.TemplateResponse(request, "_search.html", {"results": results, "q": needle})


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
    registry = request.app.state.registry
    _rebuild_links(db, registry, page)
    db.commit()
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
        registry = request.app.state.registry
        _rebuild_links(db, registry, page)
        db.commit()
    return templates.TemplateResponse(
        request, "_detail.html", _detail_ctx(request, db, campaign.id, page)
    )


@router.post("/{slug}/tags", response_class=HTMLResponse)
def add_tag(
    request: Request,
    slug: str,
    name: str = Form(""),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    page = _owned_by_slug(db, slug, campaign.id)
    if page is not None and name.strip():
        tag = db.query(Tag).filter_by(campaign_id=campaign.id, name=name.strip()).first()
        if tag is None:
            tag = Tag(campaign_id=campaign.id, name=name.strip())
            db.add(tag)
            db.flush()
        exists = db.query(WikiPageTag).filter_by(page_id=page.id, tag_id=tag.id).first() is not None
        if not exists:
            db.add(WikiPageTag(page_id=page.id, tag_id=tag.id))
        db.commit()
    return templates.TemplateResponse(
        request, "_detail.html", _detail_ctx(request, db, campaign.id, page)
    )


@router.post("/{slug}/tags/{tag_id}/delete", response_class=HTMLResponse)
def remove_tag(
    request: Request,
    slug: str,
    tag_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> HTMLResponse:
    page = _owned_by_slug(db, slug, campaign.id)
    if page is not None:
        db.query(WikiPageTag).filter_by(page_id=page.id, tag_id=tag_id).delete(
            synchronize_session=False
        )
        db.commit()
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
        db.query(WikiLink).filter_by(source_page_id=page.id).delete(synchronize_session=False)
        db.query(WikiPageTag).filter_by(page_id=page.id).delete(synchronize_session=False)
        db.delete(page)
        db.commit()
    return templates.TemplateResponse(request, "_list.html", {"pages": _pages(db, campaign.id)})
