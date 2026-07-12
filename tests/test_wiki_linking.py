from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.wiki.models import WikiLink, WikiPage

client = TestClient(create_app())


def _page(title):
    db = SessionLocal()
    try:
        return db.query(WikiPage).filter_by(title=title).first()
    finally:
        db.close()


def test_link_to_existing_page_resolves():
    client.post("/wiki", data={"title": "Link Target Alpha", "body_md": "root"})
    client.post(
        "/wiki", data={"title": "Link Source Beta", "body_md": "See [[Link Target Alpha]]."}
    )
    src = _page("Link Source Beta")
    detail = client.get(f"/wiki/{src.slug}")
    tgt = _page("Link Target Alpha")
    assert f'href="/wiki/{tgt.slug}"' in detail.text
    assert "wikilink-new" not in detail.text  # it resolved

    db = SessionLocal()
    try:
        rows = db.query(WikiLink).filter_by(source_page_id=src.id).all()
        assert any(r.target_type == "page" and r.target_id == tgt.id for r in rows)
    finally:
        db.close()


def test_unresolved_link_renders_create_link():
    client.post(
        "/wiki", data={"title": "Link Source Gamma", "body_md": "Mystery [[Nowhere Place]]."}
    )
    src = _page("Link Source Gamma")
    detail = client.get(f"/wiki/{src.slug}")
    assert "wikilink-new" in detail.text
    assert (
        "title=Nowhere" in detail.text.replace("+", " ").replace("%20", " ")
        or "Nowhere" in detail.text
    )


def test_backlinks_panel_shows_source():
    client.post("/wiki", data={"title": "Backlink Target", "body_md": "b"})
    client.post(
        "/wiki", data={"title": "Backlink Source", "body_md": "points to [[Backlink Target]]"}
    )
    tgt = _page("Backlink Target")
    detail = client.get(f"/wiki/{tgt.slug}")
    assert "Backlink Source" in detail.text
    assert "Mentioned on" in detail.text


def test_link_resolves_to_npc():
    # NPCs module is enabled; create one and link to it by name.
    client.post("/npcs", data={"name": "Wiki-Link Goblin", "disposition": "hostile"})
    client.post("/wiki", data={"title": "NPC Linker", "body_md": "meet [[Wiki-Link Goblin]]"})
    src = _page("NPC Linker")
    detail = client.get(f"/wiki/{src.slug}")
    assert "/npcs/" in detail.text
    assert "wikilink-new" not in detail.text
