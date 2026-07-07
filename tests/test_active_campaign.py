from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.campaigns import get_active_campaign
from app.core.database import Base
from app.core.models import Campaign


def _session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = Session(engine)
    # id=1 inactive "Alpha", id=2 active "Bravo"
    db.add(Campaign(id=1, name="Alpha", active=False))
    db.add(Campaign(id=2, name="Bravo", active=True))
    db.commit()
    return db


def _req(cookie: str | None) -> Request:
    headers = [(b"cookie", f"hexforge_campaign_id={cookie}".encode())] if cookie is not None else []
    return Request({"type": "http", "headers": headers})


def test_no_cookie_returns_active_row():
    db = _session()
    result = get_active_campaign(_req(None), db)
    assert result is not None
    assert result.id == 2


def test_garbage_cookie_does_not_crash_returns_active_row():
    db = _session()
    result = get_active_campaign(_req("not-a-number"), db)
    assert result is not None
    assert result.id == 2


def test_valid_cookie_returns_that_campaign():
    db = _session()
    result = get_active_campaign(_req("1"), db)
    assert result is not None
    assert result.id == 1


def test_stale_numeric_cookie_falls_back_to_active_row():
    db = _session()
    result = get_active_campaign(_req("999"), db)
    assert result is not None
    assert result.id == 2
