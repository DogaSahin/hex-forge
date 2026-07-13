from __future__ import annotations

from app.core.projection import hp_band
from app.modules.maps.models import Token


def project_tokens(tokens: list[Token]) -> list[dict]:
    """Player-safe token projection. Drops hidden + dm-layer tokens; emits an HP
    band only when explicitly shared; NEVER an HP number."""
    out: list[dict] = []
    for t in tokens:
        if not t.visible_to_players or t.layer != "tokens":
            continue
        d = {
            "id": t.id,
            "x": t.x,
            "y": t.y,
            "size": t.size,
            "color": t.color,
            "image_path": t.image_path,
            "name": t.name,
            "layer": "tokens",
        }
        if t.hp_visible_to_players and t.hp_max:
            d["hp_band"] = hp_band(t.hp_current or 0, t.hp_max)
        out.append(d)
    return out


def player_state(map_dict: dict, tokens: list[Token], fog: list[dict]) -> dict:
    return {"map": map_dict, "tokens": project_tokens(tokens), "fog": fog}
