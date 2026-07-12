from __future__ import annotations

import json

_HP_KEYS = ("hp", "hp_max", "max_hp", "hitpoints", "hit_points")
_AC_KEYS = ("ac", "armor_class", "armour_class")


def parse_stats(statblock: str | None) -> dict:
    """Best-effort HP/AC from an NPC statblock. Only JSON objects yield values;
    anything else (freeform text, JSON non-object, bad values) -> {}. Never raises."""
    if not statblock:
        return {}
    try:
        data = json.loads(statblock)
    except (ValueError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict = {}
    hp = _first_int(data, _HP_KEYS)
    ac = _first_int(data, _AC_KEYS)
    if hp is not None:
        out["hp_current"] = hp
        out["hp_max"] = hp
    if ac is not None:
        out["ac"] = ac
    return out


def _first_int(data: dict, keys: tuple[str, ...]) -> int | None:
    for key in keys:
        if key in data:
            try:
                return int(data[key])
            except (ValueError, TypeError):
                continue
    return None
