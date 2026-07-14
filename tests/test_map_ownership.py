from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.modules.maps.models import FogRegion, Map, Token

client = TestClient(create_app())


def _map_id(name: str) -> int:
    db = SessionLocal()
    try:
        row = db.query(Map).filter_by(name=name).first()
        assert row is not None
        return row.id
    finally:
        db.close()


def _token_id(map_id: int, name: str) -> int:
    tokens = client.get(f"/map/{map_id}/state").json()["tokens"]
    tid = next(t["id"] for t in tokens if t["name"] == name)
    return tid


def _other_client(campaign_name: str) -> tuple[TestClient, int]:
    """A second TestClient whose active-campaign cookie points at a brand new
    campaign, so every _owned_map/_owned_token lookup it makes resolves against
    a campaign that owns none of the objects created by `client` above."""
    db = SessionLocal()
    try:
        other = Campaign(name=campaign_name)
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()
    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    return other_client, other_id


def _cleanup_campaign(campaign_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.get(Campaign, campaign_id)
        if row is not None:
            db.delete(row)
            db.commit()
    finally:
        db.close()


def test_move_token_in_other_campaign_is_refused():
    client.post("/map", data={"name": "Ownership Move Map"})
    mid = _map_id("Ownership Move Map")
    client.post(f"/map/{mid}/token", data={"name": "Mover", "layer": "tokens"})
    tid = _token_id(mid, "Mover")

    other_client, other_id = _other_client("Ownership Other Move")
    try:
        r = other_client.post(f"/token/{tid}/move", data={"x": "999", "y": "999"})
        assert r.json() == {"ok": False}

        db = SessionLocal()
        try:
            t = db.get(Token, tid)
            assert (t.x, t.y) != (999, 999)
        finally:
            db.close()
    finally:
        _cleanup_campaign(other_id)
        client.post(f"/map/{mid}/delete")


def test_edit_token_in_other_campaign_is_refused():
    client.post("/map", data={"name": "Ownership Edit Map"})
    mid = _map_id("Ownership Edit Map")
    client.post(f"/map/{mid}/token", data={"name": "Editable", "layer": "tokens"})
    tid = _token_id(mid, "Editable")

    other_client, other_id = _other_client("Ownership Other Edit")
    try:
        other_client.post(f"/token/{tid}", data={"name": "Hijacked"})

        db = SessionLocal()
        try:
            t = db.get(Token, tid)
            assert t.name == "Editable"
        finally:
            db.close()
    finally:
        _cleanup_campaign(other_id)
        client.post(f"/map/{mid}/delete")


def test_delete_token_in_other_campaign_is_refused():
    client.post("/map", data={"name": "Ownership Delete Map"})
    mid = _map_id("Ownership Delete Map")
    client.post(f"/map/{mid}/token", data={"name": "Undeletable", "layer": "tokens"})
    tid = _token_id(mid, "Undeletable")

    other_client, other_id = _other_client("Ownership Other Delete")
    try:
        other_client.post(f"/token/{tid}/delete")

        db = SessionLocal()
        try:
            assert db.get(Token, tid) is not None
        finally:
            db.close()
    finally:
        _cleanup_campaign(other_id)
        client.post(f"/map/{mid}/delete")


def test_add_fog_on_map_in_other_campaign_is_refused():
    client.post("/map", data={"name": "Ownership Fog Map"})
    mid = _map_id("Ownership Fog Map")

    other_client, other_id = _other_client("Ownership Other Fog")
    try:
        r = other_client.post(
            f"/map/{mid}/fog",
            data={"op": "reveal", "geom": '{"type": "rect", "x": 0, "y": 0, "w": 70, "h": 70}'},
        )
        assert r.json() == {"ok": False}

        db = SessionLocal()
        try:
            assert db.query(FogRegion).filter_by(map_id=mid).count() == 0
        finally:
            db.close()
    finally:
        _cleanup_campaign(other_id)
        client.post(f"/map/{mid}/delete")


def test_player_state_for_map_in_other_campaign_is_empty_placeholder():
    client.post("/map", data={"name": "Ownership Player State Map"})
    mid = _map_id("Ownership Player State Map")
    client.post(f"/map/{mid}/token", data={"name": "ShouldNotLeak", "layer": "tokens"})

    other_client, other_id = _other_client("Ownership Other Player State")
    try:
        body = other_client.get(f"/map/{mid}/player-state").json()
        assert body == {"map": None, "tokens": [], "fog": []}
    finally:
        _cleanup_campaign(other_id)
        client.post(f"/map/{mid}/delete")
