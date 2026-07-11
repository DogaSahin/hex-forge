from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_npcs_appears_in_nav():
    assert "/npcs" in client.get("/").text


def test_npcs_page_renders_two_pane_shell():
    resp = client.get("/npcs")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="npc-detail"' in body


def test_index_hx_request_returns_roster_fragment_only():
    resp = client.get("/npcs", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert 'id="nav-rail"' not in resp.text  # fragment, not the shell
