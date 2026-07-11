from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.templating import module_templates, shell_context
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
