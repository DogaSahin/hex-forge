from fastapi.testclient import TestClient

from app.core.server import create_app
from app.modules.npcs.generator import generate_stub

client = TestClient(create_app())


def test_generate_stub_has_name_and_trait():
    stub = generate_stub()
    assert stub["name"].strip()
    assert stub["voice"].strip()  # a trait seeded into the voice field


def test_generate_route_returns_prefilled_unsaved_form():
    resp = client.get("/npcs/generate")
    assert resp.status_code == 200
    assert 'name="name"' in resp.text
    assert 'hx-post="/npcs"' in resp.text  # unsaved: posts to create, not update
