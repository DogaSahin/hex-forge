from app.core.database import SessionLocal
from app.core.models import Campaign
from app.modules.combat.models import CONDITIONS, Combatant, Encounter


def test_conditions_tuple_has_core_5e_entries():
    for expected in ("blinded", "poisoned", "prone", "stunned", "unconscious"):
        assert expected in CONDITIONS


def test_encounter_and_combatant_round_trip():
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).first()
        enc = Encounter(campaign_id=campaign.id, name="Plan-Test Model Encounter")
        db.add(enc)
        db.commit()
        db.refresh(enc)
        assert enc.round == 1 and enc.is_active is False and enc.active_combatant_id is None

        c = Combatant(encounter_id=enc.id, name="Goblin", initiative=15, hp_current=7, hp_max=7)
        db.add(c)
        db.commit()
        db.refresh(c)
        assert c.conditions_json == "[]"
        assert c.concentration is False and c.is_pc is False
        assert c.npc_id is None and c.token_id is None

        db.delete(c)
        db.delete(enc)
        db.commit()
    finally:
        db.close()
