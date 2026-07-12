import asyncio

from app.core import broadcast as bc
from app.core.broadcast import BroadcastState
from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.websocket import manager


def _new_campaign(name: str) -> int:
    db = SessionLocal()
    try:
        c = Campaign(name=name)
        db.add(c)
        db.commit()
        return c.id
    finally:
        db.close()


def _cleanup_campaign(cid: int) -> None:
    db = SessionLocal()
    try:
        db.query(BroadcastState).filter_by(campaign_id=cid).delete()
        c = db.get(Campaign, cid)
        if c is not None:
            db.delete(c)
        db.commit()
    finally:
        db.close()


def test_broadcast_state_row_round_trips():
    cid = _new_campaign("Plan-Test BC Model")
    try:
        db = SessionLocal()
        try:
            db.add(BroadcastState(campaign_id=cid, active_encounter_id=7))
            db.commit()
        finally:
            db.close()
        db = SessionLocal()
        try:
            row = db.query(BroadcastState).filter_by(campaign_id=cid).first()
            assert row is not None
            assert row.active_encounter_id == 7
            assert row.active_map_id is None
        finally:
            db.close()
    finally:
        _cleanup_campaign(cid)


def test_get_state_is_get_or_create_idempotent():
    cid = _new_campaign("Plan-Test BC GetOrCreate")
    try:
        db = SessionLocal()
        try:
            a = bc.get_state(db, cid)
            b = bc.get_state(db, cid)
            assert a.id == b.id  # one row per campaign, not duplicated
        finally:
            db.close()
    finally:
        _cleanup_campaign(cid)


def test_set_active_encounter_and_snapshot():
    cid = _new_campaign("Plan-Test BC SetActive")
    try:
        db = SessionLocal()
        try:
            bc.set_active_encounter(db, cid, 42)
            assert bc.snapshot(db, cid) == {"active_encounter_id": 42, "active_map_id": None}
            bc.set_active_encounter(db, cid, None)
            assert bc.snapshot(db, cid) == {"active_encounter_id": None, "active_map_id": None}
        finally:
            db.close()
    finally:
        _cleanup_campaign(cid)


class _FakeWS:
    def __init__(self):
        self.sent = []

    async def send_json(self, message):
        self.sent.append(message)


def test_publish_changed_is_contentless_on_broadcast_topic():
    ws = _FakeWS()
    manager.subscribe("broadcast", ws)
    try:
        asyncio.run(bc.publish_changed(99))
    finally:
        manager.unsubscribe(ws)
    assert ws.sent, "expected a publish on the broadcast topic"
    msg = ws.sent[-1]
    assert msg == {"action": "broadcast_changed", "campaign_id": 99}
    # Boundary: only action + campaign_id ride the wire — no module state.
    assert set(msg.keys()) == {"action", "campaign_id"}
