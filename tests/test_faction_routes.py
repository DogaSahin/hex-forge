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


def _make_clock(faction_name: str, segments: int = 6):
    client.post("/factions", data={"name": faction_name, "disposition": "neutral"})
    fid = _faction_id(faction_name)
    client.post(f"/factions/{fid}/clocks", data={"name": "C", "segments": str(segments)})
    db = SessionLocal()
    try:
        from app.modules.factions.models import FactionClock

        cid = db.query(FactionClock).join(Faction).filter(Faction.name == faction_name).first().id
    finally:
        db.close()
    return fid, cid


def _filled(clock_id: int) -> int:
    db = SessionLocal()
    try:
        from app.modules.factions.models import FactionClock

        return db.get(FactionClock, clock_id).filled
    finally:
        db.close()


def test_clicking_segment_fills_up_to_it():
    fid, cid = _make_clock("Plan-Test Fill")
    client.post(f"/factions/clocks/{cid}/fill", data={"segment": "3"})  # 0-based index 3 -> fill 4
    assert _filled(cid) == 4
    client.post(f"/factions/{fid}/delete")


def test_clicking_current_top_segment_unfills_it():
    fid, cid = _make_clock("Plan-Test Unfill")
    client.post(f"/factions/clocks/{cid}/fill", data={"segment": "2"})  # fill 3
    assert _filled(cid) == 3
    # click top again -> unfill to 2
    client.post(f"/factions/clocks/{cid}/fill", data={"segment": "2"})
    assert _filled(cid) == 2
    client.post(f"/factions/{fid}/delete")


def test_fill_clamps_within_bounds():
    fid, cid = _make_clock("Plan-Test FillClamp", segments=4)
    # beyond range -> clamp to 4
    client.post(f"/factions/clocks/{cid}/fill", data={"segment": "10"})
    assert _filled(cid) == 4
    client.post(f"/factions/{fid}/delete")


def test_activity_append_and_reverse_chron_feed():
    name = "Plan-Test Activity-Feed"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    client.post(f"/factions/{fid}/activity", data={"entry": "first move"})
    resp = client.post(f"/factions/{fid}/activity", data={"entry": "second move"})
    assert resp.status_code == 200
    # newest first: "second move" appears before "first move" in the rendered feed
    assert resp.text.index("second move") < resp.text.index("first move")

    # survives a fresh detail GET
    detail = client.get(f"/factions/{fid}")
    assert "first move" in detail.text and "second move" in detail.text
    client.post(f"/factions/{fid}/delete")


def test_clock_fill_refused_for_other_campaigns_faction():
    # Create a faction + clock under the default campaign.
    name = "Plan-Test Owned"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    client.post(f"/factions/{fid}/clocks", data={"name": "Secret", "segments": "6"})
    db = SessionLocal()
    try:
        from app.core.models import Campaign
        from app.modules.factions.models import FactionClock

        cid = db.query(FactionClock).filter_by(name="Secret").first().id
        # A second campaign that does NOT own this clock.
        other = Campaign(name="Plan-Test Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()

    # Request as the other campaign (cookie); the fill must be refused (no mutation).
    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/factions/clocks/{cid}/fill", data={"segment": "5"})
    assert _filled(cid) == 0  # unchanged

    # Cleanup.
    client.post(f"/factions/{fid}/delete")
    db = SessionLocal()
    try:
        from app.core.models import Campaign

        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()


def test_activity_append_writes_exactly_one_row():
    name = "Plan-Test Activity-Count"
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    fid = _faction_id(name)
    db = SessionLocal()
    try:
        from app.modules.factions.models import FactionActivity

        before = db.query(FactionActivity).count()
    finally:
        db.close()
    client.post(f"/factions/{fid}/activity", data={"entry": "one entry"})
    db = SessionLocal()
    try:
        from app.modules.factions.models import FactionActivity

        assert db.query(FactionActivity).count() == before + 1
    finally:
        db.close()
    client.post(f"/factions/{fid}/delete")
