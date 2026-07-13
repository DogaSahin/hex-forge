from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app
from app.modules.maps.geometry import clamp_hp


def test_clamp_hp():
    assert clamp_hp(120, 100) == 100
    assert clamp_hp(-5, 100) == 0
    assert clamp_hp(30, 0) == 30  # no max => floor at 0 only


def _token(client):
    # Route by name (not the last delete-link in the list) — the shared test
    # campaign accumulates maps from earlier test modules in the same run, so
    # "last in the list" is not reliably "the one this test just created".
    client.post("/map", data={"name": "EditMenuMap"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    mid = int(re.search(r'hx-get="/map/(\d+)"[^>]*>EditMenuMap</a>', txt).group(1))
    client.post(f"/map/{mid}/token", data={"name": "Old"})
    tokens = client.get(f"/map/{mid}/state").json()["tokens"]
    tid = next(t["id"] for t in tokens if t["name"] == "Old")
    return mid, tid


def test_edit_and_delete_token():
    client = TestClient(create_app())
    mid, tid = _token(client)
    client.post(
        f"/token/{tid}",
        data={
            "name": "New",
            "size": "3",
            "visible_to_players": "",
            "hp_current": "150",
            "hp_max": "100",
        },
    )
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["name"] == "New"
    assert t["size"] == 3
    assert t["visible_to_players"] is False
    assert t["hp_current"] == 100  # clamped to max

    client.post(f"/token/{tid}/delete")
    assert client.get(f"/map/{mid}/state").json()["tokens"] == []


def test_token_menu_has_hidden_inputs():
    """Menu must render hidden inputs before checkboxes for unchecked state."""
    client = TestClient(create_app())
    mid, tid = _token(client)
    resp = client.get(f"/token/{tid}/menu")
    assert 'type="hidden" name="visible_to_players"' in resp.text
    assert 'type="hidden" name="hp_visible_to_players"' in resp.text


def test_toggle_visibility_flags_off():
    """Regression: turning OFF a checkbox should persist (not silently no-op)."""
    client = TestClient(create_app())
    mid, tid = _token(client)

    # Turn on visible_to_players.
    client.post(f"/token/{tid}", data={"visible_to_players": "true"})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is True

    # Uncheck (browser sends hidden field only, since checkbox is unchecked).
    client.post(f"/token/{tid}", data={"visible_to_players": ""})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is False

    # Turn on hp_visible_to_players.
    client.post(f"/token/{tid}", data={"hp_visible_to_players": "true"})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["hp_visible_to_players"] is True

    # Uncheck (browser sends hidden field only, since checkbox is unchecked).
    client.post(f"/token/{tid}", data={"hp_visible_to_players": ""})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["hp_visible_to_players"] is False


def test_absent_checkbox_field_leaves_flag_untouched():
    """Omitting the field should leave flag unchanged (absent = untouched)."""
    client = TestClient(create_app())
    mid, tid = _token(client)

    # Set visible_to_players to True.
    client.post(f"/token/{tid}", data={"visible_to_players": "true"})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is True

    # POST with NO visible_to_players key at all (absent).
    client.post(f"/token/{tid}", data={"name": "unchanged"})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    # Flag should remain True (not touched).
    assert t["visible_to_players"] is True
