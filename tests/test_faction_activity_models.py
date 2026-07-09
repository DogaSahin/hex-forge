from app.core.database import SessionLocal
from app.modules.factions.models import Faction, FactionActivity


def test_activity_persists_with_timestamp():
    db = SessionLocal()
    try:
        cid = _campaign_id(db)
        f = Faction(campaign_id=cid, name="Plan-Test Activity")
        f.activity.append(FactionActivity(entry="raided the docks"))
        db.add(f)
        db.commit()
        db.refresh(f)
        assert f.activity[0].occurred_at is not None
        entry_id = f.activity[0].id
        db.delete(f)
        db.commit()
        assert db.get(FactionActivity, entry_id) is None  # cascade
    finally:
        db.close()


def _campaign_id(db) -> int:
    from app.core.models import Campaign

    return db.query(Campaign).order_by(Campaign.id).first().id
