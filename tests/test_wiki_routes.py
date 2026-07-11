from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.database import engine
from app.core.server import create_app

client = TestClient(create_app())


def test_wiki_tables_exist():
    tables = set(inspect(engine).get_table_names())
    assert {"wiki_page", "wiki_link", "tag", "wiki_page_tag"} <= tables


def test_wiki_appears_in_nav():
    assert "/wiki" in client.get("/").text


def test_wiki_index_renders_two_pane_shell():
    resp = client.get("/wiki")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="wiki-detail"' in body


def test_index_hx_request_returns_list_fragment_only():
    resp = client.get("/wiki", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert 'id="nav-rail"' not in resp.text
