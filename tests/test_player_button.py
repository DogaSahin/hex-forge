from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_open_player_button_present_on_dm_pages():
    for path in ("/", "/combat"):
        body = client.get(path).text
        assert "window.open('/player'" in body
        assert "Open player screen" in body
