from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.modules.combat.models import Encounter

client = TestClient(create_app())


def test_combat_appears_in_nav():
    assert "/combat" in client.get("/").text


def test_combat_index_renders_shell_with_tracker_slot():
    resp = client.get("/combat")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="tracker"' in body
    assert 'id="encounter-list"' in body


def _enc_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Encounter).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_encounter_create_view_delete_lifecycle():
    name = "Plan-Test Ambush"
    created = client.post("/combat", data={"name": name})
    assert created.status_code == 200 and name in created.text
    eid = _enc_id(name)
    assert eid is not None

    tracker = client.get(f"/combat/{eid}")
    assert name in tracker.text and 'id="tracker"' in tracker.text

    deleted = client.post(f"/combat/{eid}/delete")
    assert deleted.status_code == 200
    assert _enc_id(name) is None


def test_create_blank_name_creates_nothing():
    before = _enc_id("   ")
    resp = client.post("/combat", data={"name": "   "})
    assert resp.status_code == 200
    assert before is None  # whitespace name not persisted


def test_set_active_marks_one_and_clears_others():
    client.post("/combat", data={"name": "Plan-Test Live A"})
    client.post("/combat", data={"name": "Plan-Test Live B"})
    aid, bid = _enc_id("Plan-Test Live A"), _enc_id("Plan-Test Live B")
    client.post(f"/combat/{aid}/set-active")
    client.post(f"/combat/{bid}/set-active")
    db = SessionLocal()
    try:
        assert db.get(Encounter, aid).is_active is False
        assert db.get(Encounter, bid).is_active is True
    finally:
        db.close()
    client.post(f"/combat/{aid}/delete")
    client.post(f"/combat/{bid}/delete")


def test_encounter_in_other_campaign_is_refused():
    name = "Plan-Test Owned Encounter"
    client.post("/combat", data={"name": name})
    eid = _enc_id(name)
    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test Combat Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()
    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/combat/{eid}/delete")
    assert _enc_id(name) is not None  # not deleted by the other campaign
    db = SessionLocal()
    try:
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
    client.post(f"/combat/{eid}/delete")
