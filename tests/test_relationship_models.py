from app.core.database import SessionLocal
from app.core.models import Campaign
from app.modules.npcs.models import Relationship


def test_relationship_persists_generic_edge():
    db = SessionLocal()
    try:
        cid = db.query(Campaign).first().id
        edge = Relationship(
            campaign_id=cid,
            source_type="npc",
            source_id=1,
            target_type="faction",
            target_id=2,
            label="member of",
        )
        db.add(edge)
        db.commit()
        row = db.query(Relationship).filter_by(label="member of", campaign_id=cid).first()
        assert row.source_type == "npc" and row.target_type == "faction"
        db.delete(row)
        db.commit()
    finally:
        db.close()
