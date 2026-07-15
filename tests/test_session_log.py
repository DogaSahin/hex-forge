from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.modules.sessions.models import GameSession, SessionLog

client = TestClient(create_app())


def _make_session(title: str) -> int:
    client.post("/sessions", data={"title": title, "date": "2026-07-14"})
    db = SessionLocal()
    try:
        return db.query(GameSession).filter_by(title=title).first().id
    finally:
        db.close()


def _log_id(text: str) -> int:
    db = SessionLocal()
    try:
        return db.query(SessionLog).filter_by(text=text).first().id
    finally:
        db.close()


def _resolved_at(log_id: int):
    db = SessionLocal()
    try:
        return db.get(SessionLog, log_id).resolved_at
    finally:
        db.close()


def test_append_log_line_persists_with_tag_and_renders_newest_first():
    sid = _make_session("Plan-Test Log Session")
    client.post(f"/sessions/{sid}/log", data={"text": "the door was trapped", "tag": "combat"})
    resp = client.post(f"/sessions/{sid}/log", data={"text": "the duke lied", "tag": "roleplay"})
    assert resp.status_code == 200
    assert resp.text.index("the duke lied") < resp.text.index("the door was trapped")

    db = SessionLocal()
    try:
        row = db.query(SessionLog).filter_by(text="the door was trapped").first()
        assert row.tag == "combat"
    finally:
        db.close()

    client.post(f"/sessions/{sid}/delete")


def test_unknown_tag_is_coerced_to_none():
    sid = _make_session("Plan-Test Bad Tag Session")
    client.post(f"/sessions/{sid}/log", data={"text": "weird tag line", "tag": "sinister"})
    db = SessionLocal()
    try:
        assert db.query(SessionLog).filter_by(text="weird tag line").first().tag == "none"
    finally:
        db.close()
    client.post(f"/sessions/{sid}/delete")


def test_blank_log_line_is_not_persisted():
    sid = _make_session("Plan-Test Blank Line Session")
    db = SessionLocal()
    try:
        before = db.query(SessionLog).count()
    finally:
        db.close()
    client.post(f"/sessions/{sid}/log", data={"text": "   ", "tag": "combat"})
    db = SessionLocal()
    try:
        assert db.query(SessionLog).count() == before
    finally:
        db.close()
    client.post(f"/sessions/{sid}/delete")


def test_resolve_and_unresolve_a_thread():
    sid = _make_session("Plan-Test Thread Session")
    client.post(f"/sessions/{sid}/log", data={"text": "who poisoned the well?", "tag": "thread"})
    lid = _log_id("who poisoned the well?")
    assert _resolved_at(lid) is None  # open

    client.post(f"/sessions/log/{lid}/resolve")
    assert _resolved_at(lid) is not None  # closed

    client.post(f"/sessions/log/{lid}/unresolve")
    assert _resolved_at(lid) is None  # reopened

    client.post(f"/sessions/{sid}/delete")


def test_delete_log_line():
    sid = _make_session("Plan-Test Delete Line Session")
    client.post(f"/sessions/{sid}/log", data={"text": "delete me", "tag": "loot"})
    lid = _log_id("delete me")
    resp = client.post(f"/sessions/log/{lid}/delete")
    assert "delete me" not in resp.text
    db = SessionLocal()
    try:
        assert db.get(SessionLog, lid) is None
    finally:
        db.close()
    client.post(f"/sessions/{sid}/delete")


def test_resolve_is_a_no_op_for_a_non_thread_line():
    sid = _make_session("Plan-Test Non Thread Resolve Session")
    client.post(f"/sessions/{sid}/log", data={"text": "just a combat note", "tag": "combat"})
    lid = _log_id("just a combat note")
    assert _resolved_at(lid) is None

    client.post(f"/sessions/log/{lid}/resolve")
    assert _resolved_at(lid) is None  # not a thread line — resolve is a no-op

    client.post(f"/sessions/{sid}/delete")


def test_log_append_refused_for_another_campaigns_session():
    sid = _make_session("Plan-Test Owned Session")
    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test Other Session Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
        before = db.query(SessionLog).count()
    finally:
        db.close()

    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/sessions/{sid}/log", data={"text": "should not persist", "tag": "loot"})

    db = SessionLocal()
    try:
        assert db.query(SessionLog).count() == before  # no mutation
    finally:
        db.close()

    client.post(f"/sessions/{sid}/delete")
    db = SessionLocal()
    try:
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
