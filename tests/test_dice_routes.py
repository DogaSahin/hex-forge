from fastapi.testclient import TestClient

from app.core.server import create_app

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
