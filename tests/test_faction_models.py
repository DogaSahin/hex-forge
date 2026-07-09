from app.core.database import SessionLocal
from app.modules.factions.models import DISPOSITIONS, Faction


def test_dispositions_are_the_five_point_scale():
    assert DISPOSITIONS == ("hostile", "unfriendly", "neutral", "friendly", "allied")


def test_faction_defaults_to_neutral_and_persists():
    db = SessionLocal()
    try:
        campaign_id = _any_campaign_id(db)
        f = Faction(campaign_id=campaign_id, name="Plan-Test Iron Ring")
        db.add(f)
        db.commit()
        db.refresh(f)
        assert f.id is not None
        assert f.disposition == "neutral"
        db.delete(f)
        db.commit()
    finally:
        db.close()


def _any_campaign_id(db) -> int:
    from app.core.models import Campaign

    return db.query(Campaign).order_by(Campaign.id).first().id
