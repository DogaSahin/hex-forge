from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.modules.combat.models import Combatant, Encounter

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


def test_add_combatant_appends_row():
    client.post("/combat", data={"name": "Plan-Test Fight"})
    eid = _enc_id("Plan-Test Fight")
    resp = client.post(
        f"/combat/{eid}/combatant",
        data={"name": "Goblin", "initiative": "12", "hp_max": "7", "hp_current": "7", "ac": "13"},
    )
    assert resp.status_code == 200 and "Goblin" in resp.text
    db = SessionLocal()
    try:
        rows = db.query(Combatant).filter_by(encounter_id=eid).all()
        assert len(rows) == 1 and rows[0].hp_max == 7 and rows[0].ac == 13
    finally:
        db.close()
    client.post(f"/combat/{eid}/delete")


def test_remove_combatant_deletes_and_advances_active():
    client.post("/combat", data={"name": "Plan-Test Remove"})
    eid = _enc_id("Plan-Test Remove")
    client.post(f"/combat/{eid}/combatant", data={"name": "A", "initiative": "20"})
    client.post(f"/combat/{eid}/combatant", data={"name": "B", "initiative": "10"})
    db = SessionLocal()
    try:
        a = db.query(Combatant).filter_by(encounter_id=eid, name="A").first()
        b = db.query(Combatant).filter_by(encounter_id=eid, name="B").first()
        enc = db.get(Encounter, eid)
        enc.active_combatant_id = a.id  # A is active
        db.commit()
        a_id, b_id = a.id, b.id
    finally:
        db.close()
    client.post(f"/combat/combatant/{a_id}/delete")
    db = SessionLocal()
    try:
        assert db.get(Combatant, a_id) is None
        assert db.get(Encounter, eid).active_combatant_id == b_id  # advanced to B
    finally:
        db.close()
    client.post(f"/combat/{eid}/delete")


def test_delete_combatant_in_other_campaign_is_refused():
    client.post("/combat", data={"name": "Plan-Test Combatant Owned"})
    eid = _enc_id("Plan-Test Combatant Owned")
    client.post(
        f"/combat/{eid}/combatant",
        data={"name": "Goblin", "initiative": "15", "hp_max": "8", "hp_current": "8", "ac": "14"},
    )
    db = SessionLocal()
    try:
        combatant = db.query(Combatant).filter_by(encounter_id=eid, name="Goblin").first()
        cid = combatant.id
        other = Campaign(name="Plan-Test Combatant Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()
    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/combat/combatant/{cid}/delete")
    db = SessionLocal()
    try:
        assert db.get(Combatant, cid) is not None
    finally:
        db.close()
    db = SessionLocal()
    try:
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
    client.post(f"/combat/{eid}/delete")


def test_sort_by_initiative_orders_desc():
    client.post("/combat", data={"name": "Plan-Test Sort"})
    eid = _enc_id("Plan-Test Sort")
    client.post(f"/combat/{eid}/combatant", data={"name": "Slow", "initiative": "3"})
    client.post(f"/combat/{eid}/combatant", data={"name": "Fast", "initiative": "21"})
    client.post(f"/combat/{eid}/combatant", data={"name": "Mid", "initiative": "12"})
    client.post(f"/combat/{eid}/sort")
    db = SessionLocal()
    try:
        rows = (
            db.query(Combatant)
            .filter_by(encounter_id=eid)
            .order_by(Combatant.sort_order, Combatant.id)
            .all()
        )
        assert [r.name for r in rows] == ["Fast", "Mid", "Slow"]
    finally:
        db.close()
    client.post(f"/combat/{eid}/delete")


def test_reorder_persists_dragged_order():
    client.post("/combat", data={"name": "Plan-Test Reorder"})
    eid = _enc_id("Plan-Test Reorder")
    client.post(f"/combat/{eid}/combatant", data={"name": "One", "initiative": "10"})
    client.post(f"/combat/{eid}/combatant", data={"name": "Two", "initiative": "10"})
    db = SessionLocal()
    try:
        rows = db.query(Combatant).filter_by(encounter_id=eid).order_by(Combatant.id).all()
        one, two = rows[0].id, rows[1].id
    finally:
        db.close()
    # drag Two above One
    client.post(f"/combat/{eid}/reorder", data={"order": f"{two},{one}"})
    db = SessionLocal()
    try:
        ordered = (
            db.query(Combatant)
            .filter_by(encounter_id=eid)
            .order_by(Combatant.sort_order, Combatant.id)
            .all()
        )
        assert [r.id for r in ordered] == [two, one]
    finally:
        db.close()
    client.post(f"/combat/{eid}/delete")
