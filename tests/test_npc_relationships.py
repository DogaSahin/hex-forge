from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.npcs.models import Npc, Relationship

client = TestClient(create_app())


def _npc_id(name: str) -> int:
    db = SessionLocal()
    try:
        return db.query(Npc).filter_by(name=name).first().id
    finally:
        db.close()


def test_create_relationship_resolves_names_then_delete():
    client.post("/npcs", data={"name": "Plan-Test Rel A", "disposition": "neutral"})
    client.post("/npcs", data={"name": "Plan-Test Rel B", "disposition": "neutral"})
    a, b = _npc_id("Plan-Test Rel A"), _npc_id("Plan-Test Rel B")

    created = client.post(
        "/npcs/relationships",
        data={"source": f"npc:{a}", "target": f"npc:{b}", "label": "rival of"},
    )
    assert created.status_code == 200
    assert (
        "Plan-Test Rel A" in created.text
        and "rival of" in created.text
        and "Plan-Test Rel B" in created.text
    )

    db = SessionLocal()
    try:
        rid = db.query(Relationship).filter_by(label="rival of").first().id
    finally:
        db.close()
    deleted = client.post(f"/npcs/relationships/{rid}/delete")
    assert "rival of" not in deleted.text

    client.post(f"/npcs/{a}/delete")
    client.post(f"/npcs/{b}/delete")


def test_deleting_npc_removes_its_edges():
    client.post("/npcs", data={"name": "Plan-Test Edge Src", "disposition": "neutral"})
    client.post("/npcs", data={"name": "Plan-Test Edge Dst", "disposition": "neutral"})
    src, dst = _npc_id("Plan-Test Edge Src"), _npc_id("Plan-Test Edge Dst")
    client.post(
        "/npcs/relationships",
        data={"source": f"npc:{src}", "target": f"npc:{dst}", "label": "knows"},
    )

    client.post(f"/npcs/{src}/delete")
    db = SessionLocal()
    try:
        remaining = (
            db.query(Relationship)
            .filter(
                (Relationship.source_id == src) | (Relationship.target_id == src),
                Relationship.source_type == "npc",
            )
            .count()
        )
        assert remaining == 0
    finally:
        db.close()
    client.post(f"/npcs/{dst}/delete")


def test_relationship_rejected_for_unresolvable_endpoint():
    client.post("/npcs", data={"name": "Plan-Test Rel Solo", "disposition": "neutral"})
    solo = _npc_id("Plan-Test Rel Solo")
    db = SessionLocal()
    try:
        before = db.query(Relationship).count()
    finally:
        db.close()
    # target npc:999999 does not resolve -> no edge written
    client.post(
        "/npcs/relationships", data={"source": f"npc:{solo}", "target": "npc:999999", "label": "x"}
    )
    db = SessionLocal()
    try:
        assert db.query(Relationship).count() == before
    finally:
        db.close()
    client.post(f"/npcs/{solo}/delete")
