import pytest

from app.core.registry import DashboardCard, Metric, Registry


def test_dashboard_cards_sorted_by_order():
    reg = Registry()
    reg.add_dashboard_card(
        DashboardCard(key="b", title="B", render=lambda db, cid: "<p>b</p>", order=200)
    )
    reg.add_dashboard_card(
        DashboardCard(key="a", title="A", render=lambda db, cid: "<p>a</p>", order=100)
    )
    assert [c.key for c in reg.dashboard_cards()] == ["a", "b"]


def test_dashboard_card_defaults():
    card = DashboardCard(key="x", title="X", render=lambda db, cid: "")
    assert card.order == 100
    assert card.span == 1


def test_card_render_is_called_with_db_and_campaign():
    card = DashboardCard(key="x", title="X", render=lambda db, cid: f"<p>{cid}</p>")
    assert card.render(None, 7) == "<p>7</p>"


def test_metric_defaults_and_registration():
    reg = Registry()
    reg.add_dashboard_metric(lambda db, cid: [Metric(label="Open threads", value="3")])
    assert len(reg.metric_providers) == 1
    metric = reg.metric_providers[0](None, 1)[0]
    assert metric.label == "Open threads"
    assert metric.value == "3"
    assert metric.href is None
    assert metric.order == 100


def test_registry_starts_with_no_cards_or_metrics():
    reg = Registry()
    assert reg.dashboard_cards() == []
    assert reg.metric_providers == []


def test_add_dashboard_card_rejects_duplicate_key():
    reg = Registry()
    reg.add_dashboard_card(DashboardCard(key="dup", title="First", render=lambda db, cid: ""))
    with pytest.raises(ValueError):
        reg.add_dashboard_card(DashboardCard(key="dup", title="Second", render=lambda db, cid: ""))


def test_add_dashboard_card_allows_distinct_keys():
    reg = Registry()
    reg.add_dashboard_card(DashboardCard(key="one", title="One", render=lambda db, cid: ""))
    reg.add_dashboard_card(DashboardCard(key="two", title="Two", render=lambda db, cid: ""))
    assert [c.key for c in reg.dashboard_cards()] == ["one", "two"]
