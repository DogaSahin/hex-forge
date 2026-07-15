from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.sessions.models import GameSession

client = TestClient(create_app())


def _session_id(title: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(GameSession).filter_by(title=title).first()
        return row.id if row else None
    finally:
        db.close()


def _status(session_id: int) -> str:
    db = SessionLocal()
    try:
        return db.get(GameSession, session_id).status
    finally:
        db.close()


def test_sessions_appears_in_nav():
    assert "/sessions" in client.get("/").text


def test_sessions_page_renders_two_pane_shell():
    resp = client.get("/sessions")
    assert resp.status_code == 200
    assert 'id="nav-rail"' in resp.text
    assert 'id="session-detail"' in resp.text


def test_create_session_autonumbers_and_appears_in_list():
    title = "Plan-Test The Sunken Chapel"
    resp = client.post("/sessions", data={"title": title, "date": "2026-07-14"})
    assert resp.status_code == 200
    assert title in resp.text

    sid = _session_id(title)
    assert sid is not None
    db = SessionLocal()
    try:
        assert db.get(GameSession, sid).number >= 1  # auto-assigned, never null
    finally:
        db.close()

    client.post(f"/sessions/{sid}/delete")
    assert _session_id(title) is None


def test_activate_marks_active_and_demotes_previous():
    first, second = "Plan-Test Act One", "Plan-Test Act Two"
    client.post("/sessions", data={"title": first, "date": "2026-07-14"})
    client.post("/sessions", data={"title": second, "date": "2026-07-15"})
    fid, sid = _session_id(first), _session_id(second)

    client.post(f"/sessions/{fid}/activate")
    assert _status(fid) == "active"

    client.post(f"/sessions/{sid}/activate")
    assert _status(sid) == "active"
    assert _status(fid) == "done"

    client.post(f"/sessions/{fid}/delete")
    client.post(f"/sessions/{sid}/delete")


def test_update_session_persists_title():
    title = "Plan-Test Rename Me"
    client.post("/sessions", data={"title": title, "date": "2026-07-14"})
    sid = _session_id(title)
    renamed = "Plan-Test Renamed"
    resp = client.post(f"/sessions/{sid}", data={"title": renamed, "date": "2026-07-14"})
    assert renamed in resp.text
    assert _session_id(renamed) == sid
    client.post(f"/sessions/{sid}/delete")


def test_new_and_edit_forms_render():
    assert 'name="title"' in client.get("/sessions/new").text
    title = "Plan-Test EditForm Session"
    client.post("/sessions", data={"title": title, "date": "2026-07-14"})
    sid = _session_id(title)
    assert title in client.get(f"/sessions/{sid}/edit").text
    client.post(f"/sessions/{sid}/delete")
