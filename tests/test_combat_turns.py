from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.combat.models import Combatant, Encounter
from app.modules.combat.routes import advance_turn

client = TestClient(create_app())


def test_advance_turn_pure_logic():
    ids = [1, 2, 3]
    assert advance_turn(None, ids, 1) == (1, 1)  # start: first, no round bump
    assert advance_turn(1, ids, 1) == (2, 1)  # advance
    assert advance_turn(3, ids, 1) == (1, 2)  # wrap -> first + round++
    assert advance_turn(5, [5], 4) == (5, 5)  # single combatant self-wraps + round++
    assert advance_turn(9, ids, 1) == (1, 1)  # stale active -> first
    assert advance_turn(1, [], 1) == (None, 1)  # empty


def _enc_id(name):
    db = SessionLocal()
    try:
        r = db.query(Encounter).filter_by(name=name).first()
        return r.id if r else None
    finally:
        db.close()


def test_next_turn_cycles_and_bumps_round():
    client.post("/combat", data={"name": "Plan-Test Turns"})
    eid = _enc_id("Plan-Test Turns")
    client.post(f"/combat/{eid}/combatant", data={"name": "A", "initiative": "20"})
    client.post(f"/combat/{eid}/combatant", data={"name": "B", "initiative": "10"})
    client.post(f"/combat/{eid}/sort")  # A then B

    db = SessionLocal()
    try:
        rows = (
            db.query(Combatant)
            .filter_by(encounter_id=eid)
            .order_by(Combatant.sort_order, Combatant.id)
            .all()
        )
        a_id, b_id = rows[0].id, rows[1].id
    finally:
        db.close()

    client.post(f"/combat/{eid}/next-turn")  # -> A, round 1
    assert _active_and_round(eid) == (a_id, 1)
    client.post(f"/combat/{eid}/next-turn")  # -> B, round 1
    assert _active_and_round(eid) == (b_id, 1)
    client.post(f"/combat/{eid}/next-turn")  # wrap -> A, round 2
    assert _active_and_round(eid) == (a_id, 2)

    client.post(f"/combat/{eid}/delete")


def _active_and_round(eid):
    db = SessionLocal()
    try:
        e = db.get(Encounter, eid)
        return e.active_combatant_id, e.round
    finally:
        db.close()
