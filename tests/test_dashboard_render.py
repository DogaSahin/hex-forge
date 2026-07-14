from fastapi.testclient import TestClient

from app.core.dashboard import collect_metrics, render_cards
from app.core.registry import DashboardCard, Metric, Registry
from app.core.server import create_app


def _boom(db, campaign_id):
    raise RuntimeError("card exploded")


def test_render_cards_returns_html_in_order():
    reg = Registry()
    reg.add_dashboard_card(
        DashboardCard(key="b", title="B", render=lambda db, cid: "<p>bee</p>", order=200)
    )
    reg.add_dashboard_card(
        DashboardCard(key="a", title="A", render=lambda db, cid: "<p>ay</p>", order=100)
    )
    cards = render_cards(reg, db=None, campaign_id=1)
    assert [c["key"] for c in cards] == ["a", "b"]
    assert cards[0]["html"] == "<p>ay</p>"
    assert cards[0]["failed"] is False


def test_a_failing_card_is_isolated_and_siblings_still_render():
    reg = Registry()
    reg.add_dashboard_card(DashboardCard(key="bad", title="Bad", render=_boom, order=100))
    reg.add_dashboard_card(
        DashboardCard(key="good", title="Good", render=lambda db, cid: "<p>fine</p>", order=200)
    )
    cards = render_cards(reg, db=None, campaign_id=1)
    bad, good = cards[0], cards[1]
    assert bad["failed"] is True
    assert bad["html"] == ""
    assert good["failed"] is False
    assert good["html"] == "<p>fine</p>"


def test_collect_metrics_flattens_sorts_and_isolates_failures():
    reg = Registry()
    reg.add_dashboard_metric(lambda db, cid: [Metric(label="Late", value="1", order=200)])
    reg.add_dashboard_metric(_boom)  # raising provider must not kill the row
    reg.add_dashboard_metric(lambda db, cid: [Metric(label="Early", value="2", order=100)])
    metrics = collect_metrics(reg, db=None, campaign_id=1)
    assert [m.label for m in metrics] == ["Early", "Late"]


def test_home_renders_a_registered_card_end_to_end():
    app = create_app()
    app.state.registry.add_dashboard_card(
        DashboardCard(
            key="test.card",
            title="Plan-Test Card",
            render=lambda db, cid: "<p>plan-test-card-body</p>",
        )
    )
    client = TestClient(app)
    body = client.get("/").text
    assert 'id="dash-test-card"' in body  # dots become dashes in the DOM id
    assert "Plan-Test Card" in body
    assert "plan-test-card-body" in body


def test_home_still_renders_with_no_cards_registered():
    # A fresh app has no module cards yet; the page must still be a 200 with the shell.
    client = TestClient(create_app())
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="nav-rail"' in resp.text
