from app.modules.combat.projection import hp_band


def test_hp_band_boundaries():
    assert hp_band(0, 10) == "low"
    assert hp_band(2, 10) == "low"  # 0.20
    assert hp_band(25, 100) == "low"  # 0.25 boundary is low
    assert hp_band(26, 100) == "mid"  # just over 0.25
    assert hp_band(5, 10) == "mid"  # 0.50 boundary is mid
    assert hp_band(6, 10) == "high"  # just over 0.50
    assert hp_band(10, 10) == "high"


def test_hp_band_zero_max_is_low():
    assert hp_band(0, 0) == "low"
    assert hp_band(5, 0) == "low"
