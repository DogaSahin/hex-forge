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


def test_token_menu_flags_have_single_unambiguous_name():
    """Each visibility flag must render exactly ONE element with its name.

    The Alpine-bound hidden input is the sole carrier of the form key; the
    checkbox must have no `name` so it cannot submit a competing value.
    Duplicating the same `name` on both a hidden input and a checkbox is
    ambiguous (Starlette resolves duplicate keys to the FIRST value, not the
    last), which made it impossible to turn the flag ON. This must fail
    against the old duplicate-name template.
    """
    client = TestClient(create_app())
    mid, tid = _token(client)
    resp = client.get(f"/token/{tid}/menu")
    assert resp.text.count('name="visible_to_players"') == 1
    assert resp.text.count('name="hp_visible_to_players"') == 1


def test_toggle_visibility_flags_on():
    """Turning a flag ON: single visible_to_players="true" key must persist True.

    This is the path the duplicate-name template broke: Starlette resolves a
    duplicated form key to the FIRST value, so a hidden "" input placed before
    the checked checkbox's "true" input silently won.
    """
    client = TestClient(create_app())
    mid, tid = _token(client)

    # Force a known False starting state (visible_to_players defaults True at
    # the model level, so establish the starting point explicitly rather than
    # assume it).
    client.post(
        f"/token/{tid}",
        data={"visible_to_players": "", "hp_visible_to_players": ""},
    )
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is False
    assert t["hp_visible_to_players"] is False

    client.post(
        f"/token/{tid}",
        data={"visible_to_players": "true", "hp_visible_to_players": "true"},
    )
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is True
    assert t["hp_visible_to_players"] is True


def test_toggle_visibility_flags_off():
    """Turning a flag OFF: single visible_to_players="" key must persist False."""
    client = TestClient(create_app())
    mid, tid = _token(client)

    # Turn both flags on first.
    client.post(
        f"/token/{tid}",
        data={"visible_to_players": "true", "hp_visible_to_players": "true"},
    )
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is True
    assert t["hp_visible_to_players"] is True

    # Uncheck (Alpine sends the hidden field valued "" when unchecked).
    client.post(
        f"/token/{tid}",
        data={"visible_to_players": "", "hp_visible_to_players": ""},
    )
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["visible_to_players"] is False
    assert t["hp_visible_to_players"] is False


def test_blank_hp_fields_stay_unset():
    """Saving the token menu with blank HP fields must leave hp_current/hp_max as
    None, not silently coerce to 0. The menu always submits both fields (empty
    string when the token has no HP tracked), so a naive `_int_or(value, 0)`
    would zero out HP on every save of an HP-less token."""
    client = TestClient(create_app())
    mid, tid = _token(client)

    client.post(f"/token/{tid}", data={"hp_current": "", "hp_max": ""})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["hp_current"] is None
    assert t["hp_max"] is None


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
