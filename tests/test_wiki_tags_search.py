from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.wiki.models import Tag, WikiPage

client = TestClient(create_app())


def _page(title):
    db = SessionLocal()
    try:
        return db.query(WikiPage).filter_by(title=title).first()
    finally:
        db.close()


def test_tag_assign_and_remove():
    client.post("/wiki", data={"title": "Tag Host", "body_md": "x"})
    page = _page("Tag Host")
    added = client.post(f"/wiki/{page.slug}/tags", data={"name": "lore"})
    assert "lore" in added.text

    # Re-adding the same tag name must not duplicate the tag row.
    client.post(f"/wiki/{page.slug}/tags", data={"name": "lore"})
    db = SessionLocal()
    try:
        assert db.query(Tag).filter_by(name="lore").count() == 1
        tag = db.query(Tag).filter_by(name="lore").first()
    finally:
        db.close()

    removed = client.post(f"/wiki/{page.slug}/tags/{tag.id}/delete")
    assert "lore" not in removed.text


def test_category_and_tag_filters():
    client.post("/wiki", data={"title": "FilterA", "category": "Region", "body_md": "a"})
    client.post("/wiki", data={"title": "FilterB", "category": "Region", "body_md": "b"})
    client.post("/wiki", data={"title": "FilterC", "category": "Item", "body_md": "c"})
    pa = _page("FilterA")
    client.post(f"/wiki/{pa.slug}/tags", data={"name": "starred"})

    by_cat = client.get("/wiki", params={"category": "Item"}, headers={"HX-Request": "true"})
    assert "FilterC" in by_cat.text and "FilterA" not in by_cat.text

    by_tag = client.get("/wiki", params={"tag": "starred"}, headers={"HX-Request": "true"})
    assert "FilterA" in by_tag.text and "FilterB" not in by_tag.text
