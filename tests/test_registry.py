from fastapi import APIRouter

from app.core.registry import NavItem, Registry


def test_registry_collects_entries():
    reg = Registry()
    router = APIRouter()
    reg.add_router(router)
    reg.add_nav(NavItem(label="Dice", icon="dice", url="/dice", order=80))
    reg.add_ws_topics(["combat:1"])

    assert reg.routers == [router]
    assert reg.ws_topics == ["combat:1"]
    assert reg.nav_items[0].label == "Dice"


def test_navitem_defaults_order_100():
    assert NavItem(label="X", icon="x", url="/x").order == 100


def test_sorted_nav_orders_ascending():
    reg = Registry()
    reg.add_nav(NavItem(label="Dice", icon="dice", url="/dice", order=80))
    reg.add_nav(NavItem(label="Home", icon="home", url="/", order=10))
    assert [n.label for n in reg.sorted_nav()] == ["Home", "Dice"]
