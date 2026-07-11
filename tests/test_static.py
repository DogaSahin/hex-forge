from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_htmx_served():
    resp = client.get("/static/vendor/htmx.min.js")
    assert resp.status_code == 200
    assert len(resp.content) > 0


def test_alpine_served():
    resp = client.get("/static/vendor/alpine.min.js")
    assert resp.status_code == 200
    assert len(resp.content) > 0


def test_sortable_and_konva_served():
    assert client.get("/static/vendor/sortable.min.js").status_code == 200
    assert client.get("/static/vendor/konva.min.js").status_code == 200


def test_media_mount_serves_a_portrait_file():
    from app.core import config

    config.PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    f = config.PORTRAITS_DIR / "plan-test-media.txt"
    f.write_bytes(b"hello-media")
    try:
        from fastapi.testclient import TestClient

        from app.core.server import create_app

        resp = TestClient(create_app()).get("/media/portraits/plan-test-media.txt")
        assert resp.status_code == 200
        assert resp.content == b"hello-media"
    finally:
        f.unlink(missing_ok=True)
