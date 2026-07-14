from __future__ import annotations

from app.core.database import Base
from app.modules.maps.models import DIAGONAL_RULES, Map


def test_map_table_and_defaults():
    assert Map.__tablename__ == "map"
    cols = Base.metadata.tables["map"].columns
    # spec-required columns exist
    for name in (
        "campaign_id",
        "name",
        "image_path",
        "image_w",
        "image_h",
        "grid_size_px",
        "grid_offset_x",
        "grid_offset_y",
        "grid_visible",
        "feet_per_square",
        "diagonal_rule",
        "is_active",
    ):
        assert name in cols, f"missing column {name}"
    assert DIAGONAL_RULES == ("chebyshev", "five_ten_five", "euclidean", "manhattan")


def test_map_defaults_applied_on_flush():
    from app.core.database import SessionLocal
    from app.core.models import Campaign

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).first()
        m = Map(campaign_id=campaign.id, name="Cavern")
        db.add(m)
        db.commit()
        db.refresh(m)
        assert m.grid_size_px == 70
        assert m.feet_per_square == 5
        assert m.grid_visible is True
        assert m.diagonal_rule == "chebyshev"
        assert m.is_active is False
        assert m.image_path is None
        db.delete(m)
        db.commit()
    finally:
        db.close()
