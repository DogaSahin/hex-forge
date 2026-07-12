from fastapi.testclient import TestClient

from app.core import broadcast as bc
from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.core.websocket import manager
from app.modules.combat.models import Encounter

client = TestClient(create_app())


def _enc_id(name):
    db = SessionLocal()
    try:
        r = db.query(Encounter).filter_by(name=name).first()
        return r.id if r else None
    finally:
        db.close()


def _default_campaign_id():
    db = SessionLocal()
    try:
        return db.query(Campaign).order_by(Campaign.id).first().id
    finally:
        db.close()


class _FakeWS:
    def __init__(self):
        self.sent = []

    async def send_json(self, message):
        self.sent.append(message)


def test_set_active_updates_broadcast_and_publishes():
    client.post("/combat", data={"name": "Plan-Test BC Active"})
    eid = _enc_id("Plan-Test BC Active")
    cid = _default_campaign_id()

    ws = _FakeWS()
    manager.subscribe("broadcast", ws)
    try:
        client.post(f"/combat/{eid}/set-active")
    finally:
        manager.unsubscribe(ws)

    # Broadcast state now points at the encounter.
    db = SessionLocal()
    try:
        assert bc.snapshot(db, cid)["active_encounter_id"] == eid
    finally:
        db.close()

    # A contentless broadcast_changed signal was published.
    assert ws.sent, "expected broadcast_changed publish"
    assert ws.sent[-1] == {"action": "broadcast_changed", "campaign_id": cid}

    client.post(f"/combat/{eid}/delete")
