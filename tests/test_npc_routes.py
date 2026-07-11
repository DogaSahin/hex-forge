from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.npcs.models import Npc

client = TestClient(create_app())


def test_npcs_appears_in_nav():
    assert "/npcs" in client.get("/").text


def test_npcs_page_renders_two_pane_shell():
    resp = client.get("/npcs")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="npc-detail"' in body


def test_index_hx_request_returns_roster_fragment_only():
    resp = client.get("/npcs", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert 'id="nav-rail"' not in resp.text  # fragment, not the shell


def _npc_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Npc).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_create_detail_update_delete_lifecycle():
    name = "Plan-Test Kael Draven"
    created = client.post(
        "/npcs",
        data={"name": name, "disposition": "hostile", "motivation": "Revenge", "faction_id": ""},
    )
    assert created.status_code == 200
    assert name in created.text
    nid = _npc_id(name)
    assert nid is not None

    detail = client.get(f"/npcs/{nid}")
    assert "Revenge" in detail.text and "badge-hostile" in detail.text

    updated = client.post(f"/npcs/{nid}", data={"name": name, "disposition": "allied"})
    assert "badge-allied" in updated.text

    deleted = client.post(f"/npcs/{nid}/delete")
    assert deleted.status_code == 200
    assert _npc_id(name) is None


def test_bad_disposition_coerced_to_neutral():
    name = "Plan-Test Bad-Disp NPC"
    client.post("/npcs", data={"name": name, "disposition": "sinister"})
    db = SessionLocal()
    try:
        assert db.query(Npc).filter_by(name=name).first().disposition == "neutral"
    finally:
        db.close()
    client.post(f"/npcs/{_npc_id(name)}/delete")


def test_update_in_other_campaign_is_refused():
    from app.core.models import Campaign

    name = "Plan-Test Owned NPC"
    client.post("/npcs", data={"name": name, "disposition": "neutral"})
    nid = _npc_id(name)
    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test NPC Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()

    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/npcs/{nid}", data={"name": "HACKED", "disposition": "hostile"})
    db = SessionLocal()
    try:
        assert db.get(Npc, nid).name == name  # unchanged
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
    client.post(f"/npcs/{nid}/delete")
