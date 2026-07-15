from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.sessions.models import GameSession
from app.modules.sessions.recap import compile_recap

client = TestClient(create_app())


def _log(text, tag, minute, log_id):
    return SimpleNamespace(
        text=text, tag=tag, logged_at=datetime(2026, 7, 14, 20, minute), id=log_id
    )


def test_recap_groups_by_tag_in_fixed_heading_order():
    logs = [
        _log("looted a censer", "loot", 30, 3),
        _log("bargained with the duke", "roleplay", 10, 1),
        _log("ambushed on the bridge", "combat", 20, 2),
    ]
    out = compile_recap(logs)
    assert out.index("## Combat") < out.index("## Roleplay") < out.index("## Loot")
    assert "- ambushed on the bridge" in out


def test_recap_is_chronological_within_a_group():
    logs = [
        _log("second punch", "combat", 30, 2),
        _log("first punch", "combat", 10, 1),
    ]
    out = compile_recap(logs)
    assert out.index("first punch") < out.index("second punch")


def test_recap_skips_empty_groups_and_untagged_lines():
    logs = [
        _log("just a note", "none", 10, 1),
        _log("stabbed a goblin", "combat", 20, 2),
    ]
    out = compile_recap(logs)
    assert "## Combat" in out
    assert "## Loot" not in out  # empty group omitted entirely
    assert "just a note" not in out  # untagged lines never enter the recap


def test_recap_honors_a_tag_filter():
    logs = [
        _log("stabbed a goblin", "combat", 10, 1),
        _log("found a ring", "loot", 20, 2),
    ]
    out = compile_recap(logs, tags={"loot"})
    assert "## Loot" in out
    assert "## Combat" not in out


def test_recap_of_nothing_is_empty():
    assert compile_recap([]) == ""
    assert compile_recap([_log("x", "none", 10, 1)]) == ""


def _make_session(title: str) -> int:
    client.post("/sessions", data={"title": title, "date": "2026-07-14"})
    db = SessionLocal()
    try:
        return db.query(GameSession).filter_by(title=title).first().id
    finally:
        db.close()


def _summary(session_id: int):
    db = SessionLocal()
    try:
        return db.get(GameSession, session_id).summary
    finally:
        db.close()


def test_summary_edit_persists():
    sid = _make_session("Plan-Test Summary Session")
    resp = client.post(f"/sessions/{sid}/summary", data={"summary": "They burned the chapel."})
    assert resp.status_code == 200
    assert _summary(sid) == "They burned the chapel."
    client.post(f"/sessions/{sid}/delete")


def test_compile_previews_without_touching_summary_then_apply_writes_it():
    sid = _make_session("Plan-Test Recap Session")
    client.post(f"/sessions/{sid}/summary", data={"summary": "hand-written summary"})
    client.post(f"/sessions/{sid}/log", data={"text": "slew the ogre", "tag": "combat"})

    preview = client.post(f"/sessions/{sid}/recap", data={"tags": ["combat"]})
    assert "slew the ogre" in preview.text
    assert _summary(sid) == "hand-written summary"  # compile must NOT overwrite

    client.post(f"/sessions/{sid}/recap/apply", data={"recap": "## Combat\n- slew the ogre"})
    assert "slew the ogre" in _summary(sid)  # only the explicit apply writes

    client.post(f"/sessions/{sid}/delete")
