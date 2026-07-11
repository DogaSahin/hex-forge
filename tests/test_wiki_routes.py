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
