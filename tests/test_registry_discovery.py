from fastapi.testclient import TestClient

from app.core.server import build_registry, create_app


def test_build_registry_loads_enabled_modules():
    reg = build_registry()
    labels = [n.label for n in reg.nav_items]
    assert "Demo" in labels


def test_demo_route_is_mounted():
    client = TestClient(create_app())
    resp = client.get("/_demo")
    assert resp.status_code == 200
    assert "demo" in resp.text.lower()


def test_registry_exposed_on_app_state():
    app = create_app()
    assert any(n.url == "/_demo" for n in app.state.registry.nav_items)
