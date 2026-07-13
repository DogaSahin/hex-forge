from __future__ import annotations

import io
import re

from fastapi.testclient import TestClient
from PIL import Image

from app.core.server import create_app


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 100, 50)).save(buf, format="PNG")
    return buf.getvalue()


def _map_with_token(client):
    name = "Token Upload Map"
    client.post("/map", data={"name": name})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    m = re.search(rf'/map/(\d+)"[^>]*>{re.escape(name)}<', txt)
    assert m is not None
    mid = int(m.group(1))
    client.post(f"/map/{mid}/token", data={"name": "Ogre", "size": "2"})
    tid = client.get(f"/map/{mid}/state").json()["tokens"][0]["id"]
    return mid, tid


def test_token_image_upload_sets_path_and_kind():
    client = TestClient(create_app())
    mid, tid = _map_with_token(client)
    r = client.post(f"/token/{tid}/image", files={"image": ("ogre.png", _png(), "image/png")})
    assert r.status_code == 200
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["image_path"].startswith("tokens/")
    assert t["kind"] == "image"
