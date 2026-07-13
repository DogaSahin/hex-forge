from __future__ import annotations

from app.core.projection import hp_band
from app.modules.maps.models import Map, Token


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


def project_map(m: Map) -> dict:
    """Player-safe map fields. Explicit allow-list: a new Map column must be
    added here deliberately to ever reach the player surface."""
    return {
        "id": m.id,
        "name": m.name,
        "image_path": m.image_path,
        "image_w": m.image_w,
        "image_h": m.image_h,
        "grid_size_px": m.grid_size_px,
        "grid_offset_x": m.grid_offset_x,
        "grid_offset_y": m.grid_offset_y,
        "grid_visible": m.grid_visible,
        "feet_per_square": m.feet_per_square,
        "diagonal_rule": m.diagonal_rule,
    }


def player_state(m: Map, tokens: list[Token], fog: list[dict]) -> dict:
    return {"map": project_map(m), "tokens": project_tokens(tokens), "fog": fog}
