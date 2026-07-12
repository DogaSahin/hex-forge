from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_subscribe_frame_adds_a_second_topic_to_the_socket():
    # Connect subscribed (server-side) to "broadcast" via the query param, then
    # dynamically subscribe to "combat:777". A publish to combat:777 from THIS
    # socket must come back — proving the socket joined the topic.
    with client.websocket_connect("/ws?topic=broadcast") as ws:
        ws.send_json({"topic": "combat:777", "action": "subscribe", "payload": {}})
        ws.send_json({"topic": "combat:777", "action": "ping", "payload": {"n": 1}})
        data = ws.receive_json()
        assert data == {"topic": "combat:777", "action": "ping", "payload": {"n": 1}}


def test_subscribe_frame_is_not_echoed_as_a_message():
    # The subscribe frame itself must NOT be re-published (no handler wants it).
    # After subscribing to combat:778, the first frame received is the ping we
    # publish next — never a frame whose action is "subscribe".
    with client.websocket_connect("/ws?topic=combat:778") as ws:
        ws.send_json({"topic": "combat:778", "action": "subscribe", "payload": {}})
        ws.send_json({"topic": "combat:778", "action": "ping", "payload": {}})
        data = ws.receive_json()
        assert data["action"] == "ping"
