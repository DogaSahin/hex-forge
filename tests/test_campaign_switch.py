from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_switch_sets_cookie_and_persists():
    # create_app + migrated dev DB has at least the seeded campaign (id=1)
    resp = client.post("/campaign/switch", data={"campaign_id": "1"}, follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert client.cookies.get("hexforge_campaign_id") == "1"


def test_home_shows_campaign_selector():
    resp = client.get("/")
    assert "campaign-selector" in resp.text
