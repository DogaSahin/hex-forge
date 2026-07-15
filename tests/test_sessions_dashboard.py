from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.sessions import dashboard
from app.modules.sessions.models import GameSession, SessionLog

client = TestClient(create_app())


def _campaign_id() -> int:
    db = SessionLocal()
    try:
        from app.core.models import Campaign

        return db.query(Campaign).first().id
    finally:
        db.close()


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


def test_open_threads_card_lists_unresolved_threads_only():
    sid = _make_session("Plan-Test Threads Card Session")
    client.post(f"/sessions/{sid}/log", data={"text": "who burned the mill?", "tag": "thread"})
    client.post(f"/sessions/{sid}/log", data={"text": "a mere combat note", "tag": "combat"})

    db = SessionLocal()
    try:
        html = dashboard.render_threads_card(db, _campaign_id())
    finally:
        db.close()
    assert "who burned the mill?" in html
    assert "a mere combat note" not in html  # only thread-tagged lines

    # Resolving removes it from the card.
    client.post(f"/sessions/log/{_log_id('who burned the mill?')}/resolve")
    db = SessionLocal()
    try:
        html = dashboard.render_threads_card(db, _campaign_id())
    finally:
        db.close()
    assert "who burned the mill?" not in html

    client.post(f"/sessions/{sid}/delete")


def test_resolving_from_the_dashboard_returns_the_card_fragment():
    sid = _make_session("Plan-Test Card View Session")
    client.post(f"/sessions/{sid}/log", data={"text": "card-view thread", "tag": "thread"})
    lid = _log_id("card-view thread")

    resp = client.post(f"/sessions/log/{lid}/resolve", data={"view": "card"})
    assert resp.status_code == 200
    assert 'id="threads-card-body"' in resp.text  # the card fragment, not the log feed
    assert 'id="session-log-feed"' not in resp.text

    client.post(f"/sessions/{sid}/delete")


def test_last_session_card_shows_the_most_recent_done_session():
    sid = _make_session("Plan-Test Last Session Card")
    client.post(f"/sessions/{sid}/summary", data={"summary": "The chapel sank."})
    client.post(f"/sessions/{sid}/activate")

    # An active session isn't "last" yet — it becomes so once a newer one is activated.
    later = _make_session("Plan-Test Newer Session")
    client.post(f"/sessions/{later}/activate")  # demotes the first to done

    db = SessionLocal()
    try:
        html = dashboard.render_last_session_card(db, _campaign_id())
    finally:
        db.close()
    assert "The chapel sank." in html

    client.post(f"/sessions/{sid}/delete")
    client.post(f"/sessions/{later}/delete")


def test_metrics_report_open_thread_count():
    sid = _make_session("Plan-Test Metric Session")
    db = SessionLocal()
    try:
        before = next(
            int(m.value)
            for m in dashboard.session_metrics(db, _campaign_id())
            if m.label == "Open threads"
        )
    finally:
        db.close()

    client.post(f"/sessions/{sid}/log", data={"text": "a fresh thread", "tag": "thread"})
    db = SessionLocal()
    try:
        after = next(
            int(m.value)
            for m in dashboard.session_metrics(db, _campaign_id())
            if m.label == "Open threads"
        )
    finally:
        db.close()
    assert after == before + 1

    client.post(f"/sessions/{sid}/delete")


def test_cards_appear_on_the_home_page():
    body = client.get("/").text
    assert 'id="dash-sessions-threads"' in body
    assert 'id="dash-sessions-last"' in body
