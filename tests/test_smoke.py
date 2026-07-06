from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_smoke_page_loads_both_libs():
    resp = client.get("/smoke")
    assert resp.status_code == 200
    body = resp.text
    assert "/static/vendor/htmx.min.js" in body
    assert "/static/vendor/alpine.min.js" in body
    assert 'hx-get="/smoke/fragment"' in body
    assert "x-data" in body


def test_smoke_fragment_returns_html():
    resp = client.get("/smoke/fragment")
    assert resp.status_code == 200
    assert "swapped" in resp.text.lower()
