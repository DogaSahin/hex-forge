from __future__ import annotations

import json
import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _map_id(txt: str, name: str) -> int:
    m = re.search(rf'hx-get="/map/(\d+)"[^>]*>{re.escape(name)}</a>', txt)
    assert m is not None
    return int(m.group(1))


def test_fog_edit_publishes_contentless_map_changed():
    client = TestClient(create_app())
    client.post("/map", data={"name": "FogPublishMap"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    mid = _map_id(txt, "FogPublishMap")

    with client.websocket_connect(f"/ws?topic=map:{mid}") as ws:
        client.post(
            f"/map/{mid}/fog",
            data={
                "op": "reveal",
                "geom": json.dumps({"type": "rect", "x": 0, "y": 0, "w": 70, "h": 70}),
            },
        )
        msg = ws.receive_json()
        assert msg["action"] == "map_changed"
        assert msg["map_id"] == mid
        # Contentless by design: no fog geometry (or any other field) leaks onto the wire.
        assert set(msg.keys()) == {"action", "map_id"}
