from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_ws_echoes_message_to_same_topic():
    with client.websocket_connect("/ws?topic=combat:1") as ws:
        ws.send_json({"topic": "combat:1", "action": "ping", "payload": {"n": 1}})
        data = ws.receive_json()
        assert data == {"topic": "combat:1", "action": "ping", "payload": {"n": 1}}


def test_ws_js_served_and_dispatches_by_action():
    resp = client.get("/static/ws.js")
    assert resp.status_code == 200
    assert "action" in resp.text
    assert "connect" in resp.text
