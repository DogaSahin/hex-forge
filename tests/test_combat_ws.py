from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.core.websocket import manager
from app.modules.combat.models import Combatant, Encounter

client = TestClient(create_app())


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send_json(self, message):
        self.sent.append(message)


def _enc_id(name):
    db = SessionLocal()
    try:
        r = db.query(Encounter).filter_by(name=name).first()
        return r.id if r else None
    finally:
        db.close()


def test_mutation_publishes_contentless_signal():
    client.post("/combat", data={"name": "Plan-Test WS"})
    eid = _enc_id("Plan-Test WS")
    client.post(f"/combat/{eid}/combatant", data={"name": "T", "hp_max": "30", "hp_current": "30"})
    db = SessionLocal()
    try:
        cid = db.query(Combatant).filter_by(encounter_id=eid).first().id
    finally:
        db.close()

    ws = FakeWS()
    manager.subscribe(f"combat:{eid}", ws)
    try:
        client.post(f"/combat/combatant/{cid}/damage", data={"amount": "5"})
    finally:
        manager.unsubscribe(ws)

    assert ws.sent, "expected a publish on the combat topic"
    msg = ws.sent[-1]
    assert msg["action"] == "combat_changed"
    assert msg["encounter_id"] == eid
    # Boundary: no HP / combatant / name state may ride the wire.
    assert set(msg.keys()) == {"action", "encounter_id"}

    client.post(f"/combat/{eid}/delete")


def test_index_page_wires_the_ws_client():
    body = client.get("/combat").text
    assert "HexWS" in body and "combat_changed" in body
