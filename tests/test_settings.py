from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.settings import get_setting, set_setting


def _session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return Session(engine)


def test_get_returns_default_when_missing():
    db = _session()
    assert get_setting(db, "theme", default="dark") == "dark"


def test_set_then_get_round_trips():
    db = _session()
    set_setting(db, "theme", "dark")
    assert get_setting(db, "theme") == "dark"


def test_set_overwrites_existing():
    db = _session()
    set_setting(db, "grid", "70")
    set_setting(db, "grid", "80")
    assert get_setting(db, "grid") == "80"
