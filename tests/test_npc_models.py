from app.core.database import SessionLocal
from app.core.models import Campaign
from app.modules.npcs.models import DISPOSITIONS, Npc


def test_dispositions_are_the_five_point_ramp():
    assert DISPOSITIONS == ("hostile", "unfriendly", "neutral", "friendly", "allied")


def test_npc_persists_with_soft_faction_ref():
    db = SessionLocal()
    try:
        cid = db.query(Campaign).first().id
        npc = Npc(campaign_id=cid, name="Plan-Test Model NPC", faction_id=424242)
        db.add(npc)
        db.commit()
        row = db.query(Npc).filter_by(name="Plan-Test Model NPC").first()
        assert row.disposition == "neutral"  # server default
        assert row.faction_id == 424242  # arbitrary soft-ref, no FK constraint
        db.delete(row)
        db.commit()
    finally:
        db.close()
