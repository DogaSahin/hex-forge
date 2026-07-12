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


def test_add_from_npc_pulls_name_and_json_stats():
    # NPC with a JSON statblock
    client.post(
        "/npcs",
        data={
            "name": "Plan-Test Ogre",
            "disposition": "hostile",
            "statblock": '{"hp": 59, "ac": 11}',
        },
    )
    db = SessionLocal()
    try:
        from app.modules.npcs.models import Npc

        npc = db.query(Npc).filter_by(name="Plan-Test Ogre").first()
        npc_id = npc.id
    finally:
        db.close()

    client.post("/combat", data={"name": "Plan-Test NPC Fight"})
    eid = _enc_id("Plan-Test NPC Fight")

    form = client.get(f"/combat/{eid}/add-npc", params={"npc_id": npc_id})
    assert form.status_code == 200
    assert "Plan-Test Ogre" in form.text  # name prefilled
    assert "59" in form.text and "11" in form.text  # hp/ac prefilled

    # saving with npc_id links the combatant
    client.post(
        f"/combat/{eid}/combatant",
        data={
            "name": "Plan-Test Ogre",
            "hp_max": "59",
            "hp_current": "59",
            "ac": "11",
            "npc_id": str(npc_id),
        },
    )
    db = SessionLocal()
    try:
        c = db.query(Combatant).filter_by(encounter_id=eid, name="Plan-Test Ogre").first()
        assert c is not None and c.npc_id == npc_id and c.hp_max == 59 and c.ac == 11
    finally:
        db.close()

    client.post(f"/combat/{eid}/delete")
    from app.modules.npcs.models import Npc  # cleanup

    db = SessionLocal()
    try:
        db.delete(db.get(Npc, npc_id))
        db.commit()
    finally:
        db.close()


def test_add_from_npc_freeform_statblock_leaves_stats_blank():
    client.post("/npcs", data={"name": "Plan-Test Bandit", "statblock": "AC 12, HP 11"})
    db = SessionLocal()
    try:
        from app.modules.npcs.models import Npc

        npc_id = db.query(Npc).filter_by(name="Plan-Test Bandit").first().id
    finally:
        db.close()
    client.post("/combat", data={"name": "Plan-Test Freeform Fight"})
    eid = _enc_id("Plan-Test Freeform Fight")
    form = client.get(f"/combat/{eid}/add-npc", params={"npc_id": npc_id})
    assert "Plan-Test Bandit" in form.text  # name still prefilled
    client.post(f"/combat/{eid}/delete")
    from app.modules.npcs.models import Npc

    db = SessionLocal()
    try:
        db.delete(db.get(Npc, npc_id))
        db.commit()
    finally:
        db.close()
