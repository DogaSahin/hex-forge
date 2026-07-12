from app.modules.combat.statblock import parse_stats


def test_json_statblock_yields_hp_and_ac():
    assert parse_stats('{"hp": 22, "ac": 15}') == {"hp_current": 22, "hp_max": 22, "ac": 15}


def test_alternate_keys_recognised():
    result = parse_stats('{"max_hp": 8, "armor_class": 12}')
    assert result == {"hp_current": 8, "hp_max": 8, "ac": 12}


def test_partial_statblock_only_hp():
    assert parse_stats('{"hp": 10}') == {"hp_current": 10, "hp_max": 10}


def test_freeform_statblock_returns_empty():
    assert parse_stats("AC 13, HP 22 (5d8)") == {}


def test_none_and_junk_return_empty():
    assert parse_stats(None) == {}
    assert parse_stats("") == {}
    assert parse_stats("[1, 2, 3]") == {}  # JSON but not a dict
    assert parse_stats('{"hp": "lots"}') == {}  # non-int value ignored
