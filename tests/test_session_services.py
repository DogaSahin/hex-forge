from datetime import date

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.modules.sessions import services
from app.modules.sessions.models import GameSession


def _new(db, campaign_id, number, title):
    row = GameSession(campaign_id=campaign_id, number=number, date=date(2026, 7, 14), title=title)
    db.add(row)
    db.commit()
    return row


def test_next_number_starts_at_one_and_is_per_campaign():
    db = SessionLocal()
    try:
        a = db.query(Campaign).first()
        b = Campaign(name="Plan-Test Numbering Campaign")
        db.add(b)
        db.commit()

        assert services.next_number(db, b.id) == 1  # empty campaign starts at 1

        _new(db, b.id, 1, "Plan-Test B1")
        _new(db, b.id, 2, "Plan-Test B2")
        assert services.next_number(db, b.id) == 3

        # Campaign A is unaffected by B's numbering.
        before_a = services.next_number(db, a.id)
        _new(db, b.id, 3, "Plan-Test B3")
        assert services.next_number(db, a.id) == before_a

        for row in db.query(GameSession).filter_by(campaign_id=b.id).all():
            db.delete(row)
        db.delete(db.get(Campaign, b.id))
        db.commit()
    finally:
        db.close()


def test_activate_demotes_the_previous_active_session():
    db = SessionLocal()
    try:
        campaign = Campaign(name="Plan-Test Activate Campaign")
        db.add(campaign)
        db.commit()

        first = _new(db, campaign.id, 1, "Plan-Test First")
        second = _new(db, campaign.id, 2, "Plan-Test Second")

        services.activate(db, first)
        assert db.get(GameSession, first.id).status == "active"

        services.activate(db, second)
        assert db.get(GameSession, second.id).status == "active"
        assert db.get(GameSession, first.id).status == "done"  # demoted, not left dangling

        for row in db.query(GameSession).filter_by(campaign_id=campaign.id).all():
            db.delete(row)
        db.delete(db.get(Campaign, campaign.id))
        db.commit()
    finally:
        db.close()


def test_activating_the_already_active_session_is_idempotent():
    db = SessionLocal()
    try:
        campaign = Campaign(name="Plan-Test Idempotent Campaign")
        db.add(campaign)
        db.commit()
        only = _new(db, campaign.id, 1, "Plan-Test Only")

        services.activate(db, only)
        services.activate(db, only)  # must not demote itself to done
        assert db.get(GameSession, only.id).status == "active"

        db.delete(only)
        db.delete(db.get(Campaign, campaign.id))
        db.commit()
    finally:
        db.close()
