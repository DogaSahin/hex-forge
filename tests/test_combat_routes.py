from fastapi.testclient import TestClient

from app.core.database import SessionLocal  # noqa: F401
from app.core.models import Campaign  # noqa: F401
from app.core.server import create_app
from app.modules.combat.models import Encounter  # noqa: F401

client = TestClient(create_app())


def test_combat_appears_in_nav():
    assert "/combat" in client.get("/").text


def test_combat_index_renders_shell_with_tracker_slot():
    resp = client.get("/combat")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="tracker"' in body
    assert 'id="encounter-list"' in body
