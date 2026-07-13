from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app
from app.modules.maps.models import Map, Token
from app.modules.maps.projection import project_map, project_tokens


def _tok(**kw):
    base = dict(
        id=1,
        map_id=1,
        layer="tokens",
        kind="disc",
        x=0,
        y=0,
        size=1,
        color="#fff",
        image_path=None,
        name="T",
        hp_current=None,
        hp_max=None,
        hp_visible_to_players=False,
        visible_to_players=True,
        meta_json="{}",
    )
    base.update(kw)
    t = Token(**{k: v for k, v in base.items() if k != "id"})
    t.id = base["id"]
    return t


def test_hidden_and_dm_tokens_excluded():
    tokens = [
        _tok(id=1, name="Seen", visible_to_players=True, layer="tokens"),
        _tok(id=2, name="Hidden", visible_to_players=False, layer="tokens"),
        _tok(id=3, name="Secret", visible_to_players=True, layer="dm"),
    ]
    out = project_tokens(tokens)
    names = {o["name"] for o in out}
    assert names == {"Seen"}


def test_visible_token_included_with_expected_fields():
    tokens = [
        _tok(
            id=7,
            name="Hero",
            x=140,
            y=210,
            size=2,
            color="#abc123",
            image_path="tokens/hero.png",
        )
    ]
    out = project_tokens(tokens)
    assert len(out) == 1
    d = out[0]
    assert d == {
        "id": 7,
        "x": 140,
        "y": 210,
        "size": 2,
        "color": "#abc123",
        "image_path": "tokens/hero.png",
        "name": "Hero",
        "layer": "tokens",
    }


def test_no_hp_numbers_leak():
    tokens = [_tok(id=1, name="Wounded", hp_current=7, hp_max=30, hp_visible_to_players=True)]
    out = project_tokens(tokens)
    assert "hp_current" not in out[0]
    assert "hp_max" not in out[0]
    assert out[0]["hp_band"] == "low"  # 7/30 <= .25


def test_hp_hidden_when_flag_off():
    tokens = [_tok(id=1, hp_current=7, hp_max=30, hp_visible_to_players=False)]
    out = project_tokens(tokens)
    assert "hp_band" not in out[0]
    assert "hp_current" not in out[0]
    assert "hp_max" not in out[0]


def test_hp_band_omitted_when_hp_max_zero_or_none():
    tokens = [
        _tok(id=1, name="ZeroMax", hp_current=0, hp_max=0, hp_visible_to_players=True),
        _tok(id=2, name="NoneMax", hp_current=None, hp_max=None, hp_visible_to_players=True),
    ]
    out = project_tokens(tokens)
    assert len(out) == 2
    for d in out:
        assert "hp_band" not in d
        assert "hp_current" not in d
        assert "hp_max" not in d


def test_project_map_exact_keys_and_excludes_is_active():
    m = Map(
        id=3,
        campaign_id=1,
        name="Dungeon",
        image_path="maps/dungeon.png",
        image_w=1200,
        image_h=800,
        grid_size_px=70,
        grid_offset_x=5,
        grid_offset_y=10,
        grid_visible=True,
        feet_per_square=5,
        diagonal_rule="chebyshev",
        is_active=True,
    )
    d = project_map(m)
    assert d == {
        "id": 3,
        "name": "Dungeon",
        "image_path": "maps/dungeon.png",
        "image_w": 1200,
        "image_h": 800,
        "grid_size_px": 70,
        "grid_offset_x": 5,
        "grid_offset_y": 10,
        "grid_visible": True,
        "feet_per_square": 5,
        "diagonal_rule": "chebyshev",
    }
    assert "is_active" not in d


def _make_map(client, name):
    client.post("/map", data={"name": name})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    m = re.search(rf'/map/(\d+)"[^>]*>{re.escape(name)}<', txt)
    assert m is not None
    return int(m.group(1))


def test_player_state_endpoint_filters():
    client = TestClient(create_app())
    mid = _make_map(client, "Player State Filters")
    client.post(f"/map/{mid}/token", data={"name": "Seen", "layer": "tokens"})
    client.post(f"/map/{mid}/token", data={"name": "Secret", "layer": "dm"})
    ps = client.get(f"/map/{mid}/player-state").json()
    names = {t["name"] for t in ps["tokens"]}
    assert "Secret" not in names
    assert "Seen" in names


def test_player_state_map_has_exact_allow_listed_keys():
    client = TestClient(create_app())
    mid = _make_map(client, "Player State Map Keys")
    ps = client.get(f"/map/{mid}/player-state").json()
    assert set(ps["map"].keys()) == {
        "id",
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
    }


def test_player_state_missing_map_is_placeholder():
    client = TestClient(create_app())
    body = client.get("/map/999999/player-state").json()
    assert body == {"map": None, "tokens": [], "fog": []}


def test_player_state_no_leak_of_hp_numbers_or_secret_names():
    from app.core.database import SessionLocal

    client = TestClient(create_app())
    mid = _make_map(client, "Player State Leak Guard")

    # Visible token, no HP tracked.
    client.post(f"/map/{mid}/token", data={"name": "Visible Ally", "layer": "tokens"})
    # Hidden token (visible_to_players=False) with real HP numbers.
    client.post(f"/map/{mid}/token", data={"name": "Hidden Foe", "layer": "tokens"})
    # DM-layer secret token, distinctively named.
    client.post(f"/map/{mid}/token", data={"name": "SECRET_AMBUSH", "layer": "dm"})

    db = SessionLocal()
    try:
        hidden = db.query(Token).filter_by(map_id=mid, name="Hidden Foe").first()
        hidden.visible_to_players = False
        hidden.hp_max = 45
        hidden.hp_current = 12
        hidden.hp_visible_to_players = False

        visible = db.query(Token).filter_by(map_id=mid, name="Visible Ally").first()
        visible.hp_max = 40
        visible.hp_current = 39
        visible.hp_visible_to_players = True

        secret = db.query(Token).filter_by(map_id=mid, name="SECRET_AMBUSH").first()
        secret.hp_max = 999
        secret.hp_current = 999
        db.commit()
    finally:
        db.close()

    r = client.get(f"/map/{mid}/player-state")
    body = r.text

    assert "hp_current" not in body
    assert "hp_max" not in body
    assert "SECRET_AMBUSH" not in body
    assert "Hidden Foe" not in body
    assert "Visible Ally" in body
