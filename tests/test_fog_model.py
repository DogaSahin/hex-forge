from __future__ import annotations

from app.modules.maps.models import FogRegion


def test_fog_region_columns():
    from app.core.database import SessionLocal
    from app.core.models import Campaign
    from app.modules.maps.models import Map

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).first()
        m = Map(campaign_id=campaign.id, name="FogCols")
        db.add(m)
        db.commit()
        db.refresh(m)
        f = FogRegion(
            map_id=m.id, seq=0, op="reveal", geom_json='{"type":"rect","x":0,"y":0,"w":70,"h":70}'
        )
        db.add(f)
        db.commit()
        db.refresh(f)
        assert f.op == "reveal"
        assert f.seq == 0
        db.delete(f)
        db.delete(m)
        db.commit()
    finally:
        db.close()
