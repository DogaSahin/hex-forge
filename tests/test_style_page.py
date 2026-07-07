from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_style_page_renders_all_components():
    resp = client.get("/style")
    assert resp.status_code == 200
    body = resp.text
    for marker in [
        "btn-primary",
        "card",
        "panel",
        "row",
        "chip",
        "badge-hostile",
        "badge-wary",
        "badge-friendly",
        "hp-bar",
        "progress",
    ]:
        assert marker in body, f"missing component: {marker}"


def test_style_page_loads_dark_theme_stylesheet():
    resp = client.get("/style")
    assert 'data-theme="dark"' in resp.text
    assert "/static/app.css" in resp.text
