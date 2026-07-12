from app.core.broadcast import BroadcastState
from app.core.database import SessionLocal
from app.core.models import Campaign


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
