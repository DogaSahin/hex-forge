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


def test_entity_provider_registers_and_lists():
    reg = Registry()
    reg.add_entity_provider("faction", lambda db, cid: [(1, "Iron Circle"), (2, "The Ash")])
    assert reg.entities("faction", db=None, campaign_id=99) == [(1, "Iron Circle"), (2, "The Ash")]


def test_entities_unknown_kind_returns_empty():
    reg = Registry()
    assert reg.entities("faction", db=None, campaign_id=1) == []


def test_resolve_maps_id_to_name_and_none_for_dangling():
    reg = Registry()
    reg.add_entity_provider("faction", lambda db, cid: [(1, "Iron Circle")])
    assert reg.resolve("faction", 1, db=None, campaign_id=1) == "Iron Circle"
    assert reg.resolve("faction", 999, db=None, campaign_id=1) is None
    assert reg.resolve("npc", 1, db=None, campaign_id=1) is None
