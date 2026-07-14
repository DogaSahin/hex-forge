from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.core.websocket import manager
from app.modules.maps.models import Map

client = TestClient(create_app())


class FakeWS:
    """A bare subscriber that records what it's sent, without a real socket."""

    def __init__(self):
        self.sent = []

    async def send_json(self, message):
        self.sent.append(message)


def _map_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Map).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_subscribed_socket_receives_a_server_published_message():
    # A socket subscribed (via the query-string topic) to "broadcast" must
    # receive a message that the SERVER publishes to that topic -- here, the
    # real broadcast_changed signal fired by set-active.
    client.post("/map", data={"name": "WS Endpoint Test Map"})
    mid = _map_id("WS Endpoint Test Map")
    assert mid is not None
    try:
        with client.websocket_connect("/ws?topic=broadcast") as ws:
            client.post(f"/map/{mid}/set-active")
            data = ws.receive_json()
            assert data["action"] == "broadcast_changed"
    finally:
        client.post(f"/map/{mid}/delete")


def test_non_subscribe_frame_is_ignored_not_republished():
    # Any inbound frame whose action isn't "subscribe" must be dropped, never
    # re-published. Otherwise any socket could forge an arbitrary frame (e.g. a
    # fake token.move) onto any topic for every other subscriber to see.
    topic = "combat:998-forged-frame-test"
    sink = FakeWS()
    manager.subscribe(topic, sink)
    try:
        with client.websocket_connect(f"/ws?topic={topic}") as ws:
            ws.send_json({"topic": topic, "action": "token.move", "payload": {"x": 999, "y": 999}})
        # The `with` block doesn't return until the server has drained every
        # queued frame (the forged frame, then the disconnect that follows), so
        # if the frame had been echoed/republished, `sink` would have it by now.
        assert sink.sent == []
    finally:
        manager.unsubscribe(sink)


def test_ws_js_served_and_dispatches_by_action():
    resp = client.get("/static/ws.js")
    assert resp.status_code == 200
    assert "action" in resp.text
    assert "connect" in resp.text
