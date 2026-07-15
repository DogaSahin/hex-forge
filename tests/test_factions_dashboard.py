from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import Campaign
from app.core.server import create_app
from app.modules.factions import dashboard
from app.modules.factions.models import Faction, FactionClock

client = TestClient(create_app())


def _campaign_id() -> int:
    db = SessionLocal()
    try:
        return db.query(Campaign).first().id
    finally:
        db.close()


def _faction_id(name: str) -> int:
    db = SessionLocal()
    try:
        return db.query(Faction).filter_by(name=name).first().id
    finally:
        db.close()


def _make_faction(name: str) -> int:
    client.post("/factions", data={"name": name, "disposition": "neutral"})
    return _faction_id(name)


def _make_clock(faction_id: int, name: str, segments: int, fill_to: int) -> int:
    client.post(f"/factions/{faction_id}/clocks", data={"name": name, "segments": str(segments)})
    db = SessionLocal()
    try:
        cid = db.query(FactionClock).filter_by(name=name).first().id
    finally:
        db.close()
    if fill_to > 0:
        client.post(f"/factions/clocks/{cid}/fill", data={"segment": str(fill_to - 1)})
    return cid


def test_activity_card_shows_recent_moves():
    fid = _make_faction("Plan-Test Dash Faction")
    client.post(f"/factions/{fid}/activity", data={"entry": "seized the granary"})

    db = SessionLocal()
    try:
        html = dashboard.render_activity_card(db, _campaign_id())
    finally:
        db.close()
    assert "seized the granary" in html
    assert "Plan-Test Dash Faction" in html

    client.post(f"/factions/{fid}/delete")


def test_clocks_card_shows_near_complete_and_hides_low_ones():
    fid = _make_faction("Plan-Test Clock Faction")
    _make_clock(fid, "Plan-Test Ritual Nearly Done", segments=6, fill_to=5)  # 83% — shown
    _make_clock(fid, "Plan-Test Barely Started", segments=6, fill_to=1)  # 17% — hidden

    db = SessionLocal()
    try:
        html = dashboard.render_clocks_card(db, _campaign_id())
    finally:
        db.close()
    assert "Plan-Test Ritual Nearly Done" in html
    assert "Plan-Test Barely Started" not in html

    client.post(f"/factions/{fid}/delete")


def test_full_clocks_are_included_and_sort_first():
    fid = _make_faction("Plan-Test Full Clock Faction")
    _make_clock(fid, "Plan-Test Half Clock", segments=6, fill_to=3)  # 50%
    _make_clock(fid, "Plan-Test Fired Clock", segments=6, fill_to=6)  # 100%

    db = SessionLocal()
    try:
        html = dashboard.render_clocks_card(db, _campaign_id())
    finally:
        db.close()
    assert "Plan-Test Fired Clock" in html
    assert html.index("Plan-Test Fired Clock") < html.index("Plan-Test Half Clock")

    client.post(f"/factions/{fid}/delete")


def test_active_clocks_metric_excludes_empty_and_full_clocks():
    fid = _make_faction("Plan-Test Metric Faction")
    db = SessionLocal()
    try:
        before = int(dashboard.faction_metrics(db, _campaign_id())[0].value)
    finally:
        db.close()

    _make_clock(fid, "Plan-Test Untouched", segments=6, fill_to=0)  # empty — not active
    _make_clock(fid, "Plan-Test Finished", segments=6, fill_to=6)  # full — not active
    _make_clock(fid, "Plan-Test In Progress", segments=6, fill_to=3)  # active

    db = SessionLocal()
    try:
        metric = dashboard.faction_metrics(db, _campaign_id())[0]
    finally:
        db.close()
    assert metric.label == "Active clocks"
    assert int(metric.value) == before + 1

    client.post(f"/factions/{fid}/delete")


def test_faction_cards_appear_on_the_home_page():
    body = client.get("/").text
    assert 'id="dash-factions-activity"' in body
    assert 'id="dash-factions-clocks"' in body
