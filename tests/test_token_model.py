from __future__ import annotations

from app.modules.maps.models import Token


def test_token_defaults():
    from app.core.database import SessionLocal
    from app.core.models import Campaign
    from app.modules.maps.models import Map

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).first()
        m = Map(campaign_id=campaign.id, name="TokDefaults")
        db.add(m)
        db.commit()
        db.refresh(m)
        t = Token(map_id=m.id, x=10, y=20)
        db.add(t)
        db.commit()
        db.refresh(t)
        assert t.layer == "tokens"
        assert t.kind == "disc"
        assert t.size == 1
        assert t.visible_to_players is True
        assert t.hp_visible_to_players is False
        assert t.meta_json == "{}"
        db.delete(t)
        db.delete(m)
        db.commit()
    finally:
        db.close()
