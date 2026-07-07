from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_search_matches_nav_and_style():
    resp = client.get("/palette/search", params={"q": "sty"})
    assert resp.status_code == 200
    assert "/style" in resp.text


def test_search_is_case_insensitive_substring():
    resp = client.get("/palette/search", params={"q": "DEMO"})
    assert "/_demo" in resp.text


def test_empty_query_returns_all_entries():
    resp = client.get("/palette/search", params={"q": ""})
    assert "/style" in resp.text
    assert "/_demo" in resp.text


def test_palette_modal_present_on_shell():
    resp = client.get("/")
    body = resp.text
    assert 'id="palette"' in body
    assert "@keydown.window" in body or "keydown" in body  # Ctrl-K binding present
