from datetime import date

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.modules.sessions.models import DEFAULT_STATUS, GameSession, SessionLog


def test_session_table_exists_with_defaults():
    db = SessionLocal()
    try:
        campaign_id = db.query(Campaign).first().id
        row = GameSession(
            campaign_id=campaign_id,
            number=99,
            date=date(2026, 7, 14),
            title="Plan-Test Session Model",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        assert row.id is not None
        assert row.status == DEFAULT_STATUS  # "planned"
        assert row.summary is None

        db.delete(row)
        db.commit()
    finally:
        db.close()


def test_session_log_cascades_and_defaults():
    db = SessionLocal()
    try:
        campaign_id = db.query(Campaign).first().id
        row = GameSession(
            campaign_id=campaign_id, number=98, date=date(2026, 7, 14), title="Plan-Test Cascade"
        )
        row.logs.append(SessionLog(text="the party burned the inn", tag="combat"))
        db.add(row)
        db.commit()
        log_id = row.logs[0].id
        assert db.get(SessionLog, log_id).resolved_at is None  # open by default

        db.delete(row)  # deleting the session must take its logs with it
        db.commit()
        assert db.get(SessionLog, log_id) is None
    finally:
        db.close()


def test_logs_are_newest_first():
    db = SessionLocal()
    try:
        campaign_id = db.query(Campaign).first().id
        row = GameSession(
            campaign_id=campaign_id, number=97, date=date(2026, 7, 14), title="Plan-Test Order"
        )
        db.add(row)
        db.commit()
        row.logs.append(SessionLog(text="first line"))
        db.commit()
        row.logs.append(SessionLog(text="second line"))
        db.commit()
        db.refresh(row)
        assert row.logs[0].text == "second line"

        db.delete(row)
        db.commit()
    finally:
        db.close()
