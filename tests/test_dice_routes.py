from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.dice.models import RollHistory, SavedRoll

client = TestClient(create_app())


def test_dice_page_renders_with_nav_and_form():
    resp = client.get("/dice")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body  # full shell
    assert 'name="expression"' in body  # roll input
    assert 'hx-post="/dice/roll"' in body  # roll form wired


def test_dice_appears_in_nav():
    resp = client.get("/")
    assert "/dice" in resp.text


def _history_count() -> int:
    db = SessionLocal()
    try:
        return db.query(RollHistory).count()
    finally:
        db.close()


def test_roll_returns_breakdown_and_logs_history():
    before = _history_count()
    resp = client.post("/dice/roll", data={"expression": "2d6+3"})
    assert resp.status_code == 200
    assert "dice-total" in resp.text
    assert resp.headers.get("HX-Trigger") == "roll-logged"
    assert _history_count() == before + 1


def test_bad_expression_shows_error_not_500():
    resp = client.post("/dice/roll", data={"expression": "2d6xyz"})
    assert resp.status_code == 200
    assert "dice-error" in resp.text


def test_history_feed_survives_reload():
    client.post("/dice/roll", data={"expression": "1d20"})
    resp = client.get("/dice/history")
    assert resp.status_code == 200
    assert "history-row" in resp.text


def _saved_id(label: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(SavedRoll).filter_by(label=label).first()
        return row.id if row else None
    finally:
        db.close()


def test_create_saved_roll_then_delete():
    label = "Plan-Test-Sneak"
    create = client.post("/dice/saved", data={"label": label, "expression": "1d20+7"})
    assert create.status_code == 200
    assert label in create.text
    assert 'hx-post="/dice/roll"' in create.text  # rendered as a one-click re-roll button

    saved_id = _saved_id(label)
    assert saved_id is not None

    delete = client.post(f"/dice/saved/{saved_id}/delete")
    assert delete.status_code == 200
    assert label not in delete.text
    assert _saved_id(label) is None  # cleaned up, no leftover test rows
