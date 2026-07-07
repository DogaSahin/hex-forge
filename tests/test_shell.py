from fastapi.testclient import TestClient

from app.core.registry import NavItem
from app.core.server import create_app, templates

client = TestClient(create_app())


def test_home_renders_shell_with_brand_and_nav():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert "Hexforge" in body  # brand wordmark / title
    assert "<svg" in body  # brand mark
    assert "/_demo" in body  # registered nav item rendered


def test_active_nav_is_marked_for_current_path():
    resp = client.get("/_demo")
    assert resp.status_code == 200
    # the demo route returns only a fragment, so assert active logic via home instead
    home = client.get("/")
    assert "is-active" in home.text  # Home ("/") is active on the home page


def _render_nav(current_path: str) -> str:
    """Render the _nav.html partial standalone with a crafted context so we can
    assert the per-anchor active state (which the full-page test can't isolate)."""
    return templates.env.get_template("_nav.html").render(
        current_path=current_path,
        nav_items=[
            NavItem(label="Home", icon="home", url="/", order=0),
            NavItem(label="Demo", icon="sparkles", url="/_demo", order=900),
        ],
    )


def test_root_nav_item_not_active_on_subpage():
    """The "/" item must use exact-match, not startswith — otherwise Home would be
    active on every page (since every path startswith "/"). On /_demo, Demo is the
    active item and Home is NOT."""
    html = _render_nav(current_path="/_demo")
    assert '<a class="nav-item is-active" href="/_demo">' in html  # Demo active
    assert '<a class="nav-item" href="/">' in html  # Home rendered, not active
    assert 'is-active" href="/"' not in html  # Home never carries is-active here
