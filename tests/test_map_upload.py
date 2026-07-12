from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image

from app.core.server import create_app


def _png_bytes(w: int, h: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 20, 30)).save(buf, format="PNG")
    return buf.getvalue()


def _make_map(client: TestClient) -> int:
    import re

    client.post("/map", data={"name": "Upload Target"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    return int(re.findall(r"/map/(\d+)/delete", txt)[-1])


def test_image_upload_stores_path_and_dims():
    client = TestClient(create_app())
    mid = _make_map(client)
    files = {"image": ("battle.png", _png_bytes(320, 200), "image/png")}
    r = client.post(f"/map/{mid}/image", files=files)
    assert r.status_code == 200
    state = client.get(f"/map/{mid}/state").json()
    assert state["map"]["image_path"].startswith("maps/")
    assert state["map"]["image_w"] == 320
    assert state["map"]["image_h"] == 200


def test_unsupported_type_rejected():
    client = TestClient(create_app())
    mid = _make_map(client)
    files = {"image": ("notes.txt", b"hello", "text/plain")}
    client.post(f"/map/{mid}/image", files=files)
    # request succeeds but image is not stored
    state = client.get(f"/map/{mid}/state").json()
    assert state["map"]["image_path"] is None
