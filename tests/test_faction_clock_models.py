from app.core.database import SessionLocal
from app.modules.factions.models import Faction, FactionClock


def test_clock_persists_and_defaults():
    db = SessionLocal()
    try:
        cid = _campaign_id(db)
        f = Faction(campaign_id=cid, name="Plan-Test Clockholder")
        db.add(f)
        db.commit()
        clock = FactionClock(faction_id=f.id, name="Ritual", segments=6)
        db.add(clock)
        db.commit()
        db.refresh(clock)
        assert clock.filled == 0
        db.delete(f)
        db.commit()
    finally:
        db.close()


def test_deleting_faction_cascades_clocks():
    db = SessionLocal()
    try:
        cid = _campaign_id(db)
        f = Faction(campaign_id=cid, name="Plan-Test Cascade")
        f.clocks.append(FactionClock(name="Doom", segments=4))
        db.add(f)
        db.commit()
        clock_id = f.clocks[0].id
        db.delete(f)
        db.commit()
        assert db.get(FactionClock, clock_id) is None
    finally:
        db.close()


def _campaign_id(db) -> int:
    from app.core.models import Campaign

    return db.query(Campaign).order_by(Campaign.id).first().id
