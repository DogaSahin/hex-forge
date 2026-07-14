from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.core.websocket import manager
from app.modules.combat.models import Encounter

client = TestClient(create_app())


class FakeWS:
    """A bare subscriber that records what it's sent, without a real socket."""

    def __init__(self):
        self.sent = []

    async def send_json(self, message):
        self.sent.append(message)


def _enc_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Encounter).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_subscribe_frame_adds_a_second_topic_to_the_socket():
    # Connect subscribed (server-side) to "broadcast" via the query param, then
    # dynamically subscribe to a fresh combat topic the socket never connected
    # with. A real server-published message (fired by a genuine combat route,
    # not an echo) arriving on that topic proves the dynamic subscribe worked.
    client.post("/combat", data={"name": "WS Subscribe Dynamic Topic"})
    eid = _enc_id("WS Subscribe Dynamic Topic")
    assert eid is not None
    try:
        with client.websocket_connect("/ws?topic=broadcast") as ws:
            ws.send_json({"topic": f"combat:{eid}", "action": "subscribe", "payload": {}})
            client.post(
                f"/combat/{eid}/combatant",
                data={"name": "T", "hp_max": "10", "hp_current": "10"},
            )
            data = ws.receive_json()
            assert data["action"] == "combat_changed"
            assert data["encounter_id"] == eid
    finally:
        client.post(f"/combat/{eid}/delete")


def test_subscribe_frame_itself_produces_no_message():
    # The subscribe frame must not itself trigger any publish. Proven by a
    # second subscriber on the same topic, which must see nothing as a result
    # of another socket's subscribe frame alone.
    topic = "combat:999-subscribe-only-test"
    sink = FakeWS()
    manager.subscribe(topic, sink)
    try:
        with client.websocket_connect("/ws?topic=broadcast") as ws:
            ws.send_json({"topic": topic, "action": "subscribe", "payload": {}})
        assert sink.sent == []
    finally:
        manager.unsubscribe(sink)
