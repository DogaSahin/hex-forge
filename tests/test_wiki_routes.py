from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.database import SessionLocal, engine
from app.core.server import create_app
from app.modules.wiki.models import WikiPage

client = TestClient(create_app())


def test_wiki_tables_exist():
    tables = set(inspect(engine).get_table_names())
    assert {"wiki_page", "wiki_link", "tag", "wiki_page_tag"} <= tables


def test_wiki_appears_in_nav():
    assert "/wiki" in client.get("/").text


def test_wiki_index_renders_two_pane_shell():
    resp = client.get("/wiki")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="wiki-detail"' in body


def test_index_hx_request_returns_list_fragment_only():
    resp = client.get("/wiki", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert 'id="nav-rail"' not in resp.text


def _page_by_title(title):
    db = SessionLocal()
    try:
        return db.query(WikiPage).filter_by(title=title).first()
    finally:
        db.close()


def test_create_detail_update_delete_lifecycle():
    title = "Plan-Test Sunless Citadel"
    created = client.post(
        "/wiki", data={"title": title, "category": "Location", "body_md": "A **deep** ruin."}
    )
    assert created.status_code == 200
    assert "<strong>deep</strong>" in created.text  # markdown rendered on detail
    page = _page_by_title(title)
    assert page is not None and page.slug == "plan-test-sunless-citadel"

    detail = client.get(f"/wiki/{page.slug}")
    assert title in detail.text and "<strong>deep</strong>" in detail.text

    updated = client.post(
        f"/wiki/{page.slug}",
        data={"title": title, "category": "Dungeon", "body_md": "Now *cleared*."},
    )
    assert "<em>cleared</em>" in updated.text

    deleted = client.post(f"/wiki/{page.slug}/delete")
    assert deleted.status_code == 200
    assert _page_by_title(title) is None


def test_slug_uniqueness_within_campaign():
    client.post("/wiki", data={"title": "Dup Town", "body_md": ""})
    client.post("/wiki", data={"title": "Dup Town", "body_md": ""})
    db = SessionLocal()
    try:
        slugs = [p.slug for p in db.query(WikiPage).filter(WikiPage.title == "Dup Town").all()]
    finally:
        db.close()
    assert "dup-town" in slugs and "dup-town-2" in slugs


def test_create_requires_title():
    resp = client.post("/wiki", data={"title": "   ", "body_md": "x"})
    assert resp.status_code == 200
    assert "Title is required" in resp.text


def test_wiki_update_in_other_campaign_is_refused():
    from app.core.models import Campaign

    title = "Plan-Test Owned Wiki Page"
    client.post("/wiki", data={"title": title, "body_md": "orig"})
    page = _page_by_title(title)
    assert page is not None
    page_id = page.id
    slug = page.slug

    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test Wiki Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()

    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/wiki/{slug}", data={"title": "HACKED", "body_md": "x"})
    db = SessionLocal()
    try:
        updated_page = db.get(WikiPage, page_id)
        assert updated_page.title == title  # unchanged
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
    client.post(f"/wiki/{slug}/delete")


def test_wiki_delete_in_other_campaign_is_refused():
    from app.core.models import Campaign

    title = "Plan-Test Wiki Delete Test"
    client.post("/wiki", data={"title": title, "body_md": "x"})
    page = _page_by_title(title)
    assert page is not None
    page_id = page.id
    slug = page.slug

    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test Wiki Other Campaign Delete")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()

    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/wiki/{slug}/delete")
    db = SessionLocal()
    try:
        assert db.get(WikiPage, page_id) is not None  # still exists
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
    client.post(f"/wiki/{slug}/delete")


def test_update_requires_title():
    title = "Plan-Test Update Title Validation"
    client.post("/wiki", data={"title": title, "body_md": "orig"})
    page = _page_by_title(title)
    assert page is not None
    slug = page.slug

    resp = client.post(f"/wiki/{slug}", data={"title": "   ", "body_md": "x"})
    assert resp.status_code == 200
    assert "Title is required" in resp.text
    updated_page = _page_by_title(title)
    assert updated_page is not None and updated_page.title == title
    client.post(f"/wiki/{slug}/delete")
