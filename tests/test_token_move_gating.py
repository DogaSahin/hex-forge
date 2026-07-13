from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _map_id(txt: str, name: str) -> int:
    # Route by unique name — the shared test campaign accumulates maps across test
    # modules in the same run, so "last link in the list" is not reliably "the one
    # this test just created".
    m = re.search(rf'hx-get="/map/(\d+)"[^>]*>{re.escape(name)}</a>', txt)
    assert m is not None
    return int(m.group(1))


def _setup(client: TestClient, map_name: str) -> tuple[int, int, int, int]:
    """Build a map with three tokens: a visible tokens-layer token ("Vis"), a
    dm-layer/secret token ("Sec"), and a hidden tokens-layer token ("Hid",
    visible_to_players explicitly turned off)."""
    client.post("/map", data={"name": map_name})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    mid = _map_id(txt, map_name)

    client.post(f"/map/{mid}/token", data={"name": "Vis", "layer": "tokens"})
    client.post(f"/map/{mid}/token", data={"name": "Sec", "layer": "dm"})
    client.post(f"/map/{mid}/token", data={"name": "Hid", "layer": "tokens"})

    tokens = client.get(f"/map/{mid}/state").json()["tokens"]
    vis = next(t["id"] for t in tokens if t["name"] == "Vis")
    sec = next(t["id"] for t in tokens if t["name"] == "Sec")
    hid = next(t["id"] for t in tokens if t["name"] == "Hid")

    # "" clears the flag: bool("") is False, whereas any non-empty string is truthy.
    client.post(f"/token/{hid}", data={"visible_to_players": ""})

    return mid, vis, sec, hid


def test_visible_token_move_publishes_on_player_topic():
    client = TestClient(create_app())
    mid, vis, _sec, _hid = _setup(client, "GateMapVisible")
    with client.websocket_connect(f"/ws?topic=map:{mid}") as player_ws:
        client.post(f"/token/{vis}/move", data={"x": "111", "y": "222"})
        msg = player_ws.receive_json()
        assert msg["action"] == "token.move"
        assert msg["map_id"] == mid
        assert msg["token_id"] == vis
        assert msg["x"] == 111
        assert msg["y"] == 222


def test_dm_layer_token_move_reaches_dm_topic():
    client = TestClient(create_app())
    mid, _vis, sec, _hid = _setup(client, "GateMapDmLayer")
    with client.websocket_connect(f"/ws?topic=map:{mid}:dm") as dm_ws:
        client.post(f"/token/{sec}/move", data={"x": "33", "y": "44"})
        msg = dm_ws.receive_json()
        assert msg["action"] == "token.move"
        assert msg["token_id"] == sec
        assert msg["x"] == 33
        assert msg["y"] == 44


def test_hidden_token_move_reaches_dm_topic():
    client = TestClient(create_app())
    mid, _vis, _sec, hid = _setup(client, "GateMapHiddenDm")
    with client.websocket_connect(f"/ws?topic=map:{mid}:dm") as dm_ws:
        client.post(f"/token/{hid}/move", data={"x": "5", "y": "6"})
        msg = dm_ws.receive_json()
        assert msg["action"] == "token.move"
        assert msg["token_id"] == hid
        assert msg["x"] == 5
        assert msg["y"] == 6


def test_hidden_and_dm_layer_moves_never_reach_player_topic():
    """The security boundary: a hidden token's (or a dm-layer token's) coordinates must
    never appear on the player-safe topic. Instead of relying on a timeout to prove
    "nothing arrived", move the hidden and dm-layer tokens first, then move the visible
    token — the first (and only) message the player socket receives must be for the
    visible token, proving the earlier moves never rode that topic."""
    client = TestClient(create_app())
    mid, vis, sec, hid = _setup(client, "GateMapNoLeak")
    with client.websocket_connect(f"/ws?topic=map:{mid}") as player_ws:
        client.post(f"/token/{hid}/move", data={"x": "10", "y": "10"})
        client.post(f"/token/{sec}/move", data={"x": "20", "y": "20"})
        client.post(f"/token/{vis}/move", data={"x": "77", "y": "88"})

        msg = player_ws.receive_json()
        assert msg["action"] == "token.move"
        assert msg["token_id"] == vis
        assert msg["x"] == 77
        assert msg["y"] == 88
