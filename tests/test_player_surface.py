from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.combat.models import Encounter

client = TestClient(create_app())


def _enc_id(name):
    db = SessionLocal()
    try:
        r = db.query(Encounter).filter_by(name=name).first()
        return r.id if r else None
    finally:
        db.close()


def test_player_shell_is_standalone_read_only():
    body = client.get("/player").text
    # No DM chrome on the player surface.
    assert 'id="nav-rail"' not in body
    assert "_campaign_selector" not in body
    assert 'id="palette"' not in body
    # It wires the WS client + the broadcast topic.
    assert "HexWS" in body
    assert "broadcast_changed" in body
    assert "/player/state" in body
    # The dm-only map topic attribute is the sole authorization for map:{id}:dm — the
    # player shell must never emit it, and must always mount in player mode.
    assert "data-dm-topic" not in body
    assert 'dataset.mode = "player"' in body


def test_player_state_reflects_set_active():
    client.post("/combat", data={"name": "Plan-Test Player State"})
    eid = _enc_id("Plan-Test Player State")
    client.post(f"/combat/{eid}/set-active")
    state = client.get("/player/state").json()
    assert state["active_encounter_id"] == eid
    assert "active_map_id" in state
    client.post(f"/combat/{eid}/delete")
