from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_factions_appears_in_nav():
    resp = client.get("/")
    assert "/factions" in resp.text


def test_factions_page_renders_two_pane_shell():
    resp = client.get("/factions")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body  # full shell
    assert 'id="faction-detail"' in body  # detail pane slot
