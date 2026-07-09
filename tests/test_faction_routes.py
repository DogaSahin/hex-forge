from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.factions.models import Faction

client = TestClient(create_app())


def test_factions_appears_in_nav():
    resp = client.get("/")
    assert "/factions" in resp.text


def test_factions_page_renders_two_pane_shell():
    resp = client.get("/factions")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body  # full shell
    assert 'id="faction-detail"' in body  # detail pane slot


def _faction_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Faction).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_create_faction_then_appears_in_roster_and_delete():
    name = "Plan-Test Cult of Ash"
    create = client.post(
        "/factions",
        data={"name": name, "disposition": "hostile", "goals": "Burn it down", "description": ""},
    )
    assert create.status_code == 200
    assert name in create.text
    assert "badge-hostile" in create.text  # disposition badge rendered
    fid = _faction_id(name)
    assert fid is not None

    delete = client.post(f"/factions/{fid}/delete")
    assert delete.status_code == 200
    assert _faction_id(name) is None


def test_update_faction_changes_disposition():
    name = "Plan-Test Merchants"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    resp = client.post(
        f"/factions/{fid}", data={"name": name, "disposition": "allied", "goals": "Profit"}
    )
    assert resp.status_code == 200
    assert "badge-allied" in resp.text
    client.post(f"/factions/{fid}/delete")


def test_bad_disposition_is_coerced_not_persisted():
    name = "Plan-Test Bad-Disp"
    resp = client.post("/factions", data={"name": name, "disposition": "sinister"})
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        row = db.query(Faction).filter_by(name=name).first()
        assert row.disposition == "neutral"  # unknown value coerced to default
    finally:
        db.close()
    client.post(f"/factions/{_faction_id(name)}/delete")


def test_new_form_and_edit_form_render():
    assert 'name="disposition"' in client.get("/factions/new").text
    name = "Plan-Test EditForm"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    edit = client.get(f"/factions/{fid}/edit")
    assert name in edit.text and 'name="disposition"' in edit.text
    client.post(f"/factions/{fid}/delete")


def test_clock_create_and_delete():
    name = "Plan-Test Clocks-Faction"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    created = client.post(f"/factions/{fid}/clocks", data={"name": "Ritual", "segments": "6"})
    assert created.status_code == 200
    assert "Ritual" in created.text
    assert created.text.count("clock-seg") == 6  # six segments rendered

    db = SessionLocal()
    try:
        from app.modules.factions.models import FactionClock

        clock_id = db.query(FactionClock).filter_by(name="Ritual").first().id
    finally:
        db.close()
    deleted = client.post(f"/factions/clocks/{clock_id}/delete")
    assert deleted.status_code == 200
    assert "Ritual" not in deleted.text
    client.post(f"/factions/{fid}/delete")


def test_clock_segments_clamped_to_range():
    name = "Plan-Test Clamp-Clock"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    resp = client.post(f"/factions/{fid}/clocks", data={"name": "Huge", "segments": "999"})
    assert resp.text.count("clock-seg") == 12  # clamped to max 12
    client.post(f"/factions/{fid}/delete")
