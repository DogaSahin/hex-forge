from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.combat.models import Combatant, Encounter

client = TestClient(create_app())


def _enc_id(name):
    db = SessionLocal()
    try:
        r = db.query(Encounter).filter_by(name=name).first()
        return r.id if r else None
    finally:
        db.close()


def _setup_wounded_monster():
    client.post("/combat", data={"name": "Plan-Test Mirror"})
    eid = _enc_id("Plan-Test Mirror")
    client.post(
        f"/combat/{eid}/combatant",
        data={"name": "Ogre", "initiative": "9", "hp_max": "59", "hp_current": "7", "ac": "11"},
    )
    db = SessionLocal()
    try:
        cid = db.query(Combatant).filter_by(encounter_id=eid).first().id
    finally:
        db.close()
    client.post(f"/combat/combatant/{cid}/condition", data={"name": "prone", "op": "add"})
    return eid


def test_player_mirror_shows_name_and_band_only():
    eid = _setup_wounded_monster()
    try:
        body = client.get(f"/combat/{eid}/player").text
        assert "Ogre" in body  # names are shared
        assert 'data-band="low"' in body  # 7/59 ~ 0.12 -> low band shown
        # Two-surface boundary — assert the DM-only leak vectors are absent.
        # (Anchor to markup, not bare digits, which collide with ids/round numbers.)
        assert "7/59" not in body  # the DM hp_current/hp_max text
        assert "hp-text" not in body  # no numeric HP span
        assert "hp-input" not in body  # no DM damage/heal inputs
        assert "ac-input" not in body  # no AC field
        assert "prone" not in body  # conditions never leak
        assert "/damage" not in body and "/heal" not in body and "/ac" not in body
    finally:
        client.post(f"/combat/{eid}/delete")


def test_player_mirror_missing_encounter_is_placeholder():
    body = client.get("/combat/99999/player").text
    assert "Nothing is being shared" in body
