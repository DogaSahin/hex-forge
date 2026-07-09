from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.models import Campaign
from app.modules.dice.models import RollHistory, SavedRoll


def _session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add(Campaign(id=1, name="Alpha", active=True))
    db.commit()
    return db


def test_saved_roll_round_trips():
    db = _session()
    db.add(SavedRoll(campaign_id=1, label="Fireball", expression="8d6"))
    db.commit()
    row = db.query(SavedRoll).one()
    assert row.label == "Fireball" and row.expression == "8d6"


def test_roll_history_round_trips_and_defaults_timestamp():
    db = _session()
    db.add(RollHistory(campaign_id=1, expression="1d20+5", result=17, breakdown_json="{}"))
    db.commit()
    row = db.query(RollHistory).one()
    assert row.result == 17
    assert row.rolled_at is not None
