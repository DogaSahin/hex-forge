from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.modules.maps.models import Map

client = TestClient(create_app())


def _map_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Map).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_set_active_updates_broadcast_and_clears_others():
    client.post("/map", data={"name": "Plan-Test Active Alpha"})
    client.post("/map", data={"name": "Plan-Test Active Beta"})
    a = _map_id("Plan-Test Active Alpha")
    b = _map_id("Plan-Test Active Beta")
    assert a is not None and b is not None

    client.post(f"/map/{a}/set-active")
    assert client.get("/player/state").json()["active_map_id"] == a

    client.post(f"/map/{b}/set-active")
    ps = client.get("/player/state").json()
    assert ps["active_map_id"] == b

    # only one active at a time
    assert client.get(f"/map/{a}/state").json()["map"]["is_active"] is False
    assert client.get(f"/map/{b}/state").json()["map"]["is_active"] is True

    client.post(f"/map/{a}/delete")
    client.post(f"/map/{b}/delete")


def test_set_active_publishes_contentless_broadcast_changed():
    client.post("/map", data={"name": "Plan-Test Active Publish"})
    mid = _map_id("Plan-Test Active Publish")
    assert mid is not None

    with client.websocket_connect("/ws?topic=broadcast") as ws:
        client.post(f"/map/{mid}/set-active")
        msg = ws.receive_json()
        assert msg["action"] == "broadcast_changed"
        # Contentless by design: no map id, name, or any other map content leaks onto
        # the wire. The player refetches its own snapshot via /player/state.
        assert set(msg.keys()) == {"action", "campaign_id"}

    client.post(f"/map/{mid}/delete")


def test_set_active_refused_for_map_in_other_campaign():
    client.post("/map", data={"name": "Plan-Test Active Owned"})
    mid = _map_id("Plan-Test Active Owned")
    assert mid is not None

    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test Active Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()

    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/map/{mid}/set-active")

    db = SessionLocal()
    try:
        assert db.get(Map, mid).is_active is False
    finally:
        db.close()

    db = SessionLocal()
    try:
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()

    client.post(f"/map/{mid}/delete")


def test_delete_active_map_clears_broadcast_pointer_and_publishes():
    client.post("/map", data={"name": "Plan-Test Active Delete Live"})
    mid = _map_id("Plan-Test Active Delete Live")
    assert mid is not None

    client.post(f"/map/{mid}/set-active")
    assert client.get("/player/state").json()["active_map_id"] == mid

    with client.websocket_connect("/ws?topic=broadcast") as ws:
        client.post(f"/map/{mid}/delete")
        msg = ws.receive_json()
        assert msg["action"] == "broadcast_changed"

    # The pointer must be cleared, not left dangling (ids are reused, so a stale
    # pointer could later resolve to an unrelated, un-pushed map).
    assert client.get("/player/state").json()["active_map_id"] is None
