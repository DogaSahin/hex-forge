from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.sessions.models import GameSession

client = TestClient(create_app())


def _make_session_with_secrets() -> int:
    title = "Plan-Test Boundary Session"
    client.post("/sessions", data={"title": title, "date": "2026-07-14"})
    db = SessionLocal()
    try:
        sid = db.query(GameSession).filter_by(title=title).first().id
    finally:
        db.close()
    client.post(f"/sessions/{sid}/summary", data={"summary": "The duke is the traitor."})
    client.post(f"/sessions/{sid}/log", data={"text": "the vault code is 7719", "tag": "thread"})
    return sid


def test_player_state_key_set_is_an_exact_allowlist():
    """Fails closed: any new key on the player payload trips this until reviewed."""
    sid = _make_session_with_secrets()
    state = client.get("/player/state").json()
    assert set(state.keys()) == {"active_encounter_id", "active_map_id"}
    client.post(f"/sessions/{sid}/delete")


def test_player_state_carries_no_session_content():
    sid = _make_session_with_secrets()
    flat = str(client.get("/player/state").json()).lower()
    assert "traitor" not in flat  # the summary must never cross
    assert "7719" not in flat  # nor the log line
    client.post(f"/sessions/{sid}/delete")


def test_player_shell_never_renders_session_content():
    sid = _make_session_with_secrets()
    body = client.get("/player").text
    assert "traitor" not in body
    assert "7719" not in body
    assert "/sessions" not in body  # sessions is not linked from the player surface
    client.post(f"/sessions/{sid}/delete")


def test_sessions_registers_no_ws_topic():
    app = create_app()
    assert not any(t.startswith("session") for t in app.state.registry.ws_topics)
