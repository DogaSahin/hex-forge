import io

from fastapi.testclient import TestClient

from app.core import config
from app.core.database import SessionLocal
from app.core.server import create_app
from app.modules.npcs.models import Npc

client = TestClient(create_app())


def test_npcs_appears_in_nav():
    assert "/npcs" in client.get("/").text


def test_npcs_page_renders_two_pane_shell():
    resp = client.get("/npcs")
    assert resp.status_code == 200
    body = resp.text
    assert 'id="nav-rail"' in body
    assert 'id="npc-detail"' in body


def test_index_hx_request_returns_roster_fragment_only():
    resp = client.get("/npcs", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert 'id="nav-rail"' not in resp.text  # fragment, not the shell


def _npc_id(name: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.query(Npc).filter_by(name=name).first()
        return row.id if row else None
    finally:
        db.close()


def test_create_detail_update_delete_lifecycle():
    name = "Plan-Test Kael Draven"
    created = client.post(
        "/npcs",
        data={"name": name, "disposition": "hostile", "motivation": "Revenge", "faction_id": ""},
    )
    assert created.status_code == 200
    assert name in created.text
    nid = _npc_id(name)
    assert nid is not None

    detail = client.get(f"/npcs/{nid}")
    assert "Revenge" in detail.text and "badge-hostile" in detail.text

    updated = client.post(f"/npcs/{nid}", data={"name": name, "disposition": "allied"})
    assert "badge-allied" in updated.text

    deleted = client.post(f"/npcs/{nid}/delete")
    assert deleted.status_code == 200
    assert _npc_id(name) is None


def test_bad_disposition_coerced_to_neutral():
    name = "Plan-Test Bad-Disp NPC"
    client.post("/npcs", data={"name": name, "disposition": "sinister"})
    db = SessionLocal()
    try:
        assert db.query(Npc).filter_by(name=name).first().disposition == "neutral"
    finally:
        db.close()
    client.post(f"/npcs/{_npc_id(name)}/delete")


def test_update_in_other_campaign_is_refused():
    from app.core.models import Campaign

    name = "Plan-Test Owned NPC"
    client.post("/npcs", data={"name": name, "disposition": "neutral"})
    nid = _npc_id(name)
    db = SessionLocal()
    try:
        other = Campaign(name="Plan-Test NPC Other Campaign")
        db.add(other)
        db.commit()
        other_id = other.id
    finally:
        db.close()

    other_client = TestClient(create_app())
    other_client.cookies.set("hexforge_campaign_id", str(other_id))
    other_client.post(f"/npcs/{nid}", data={"name": "HACKED", "disposition": "hostile"})
    db = SessionLocal()
    try:
        assert db.get(Npc, nid).name == name  # unchanged
        db.delete(db.get(Campaign, other_id))
        db.commit()
    finally:
        db.close()
    client.post(f"/npcs/{nid}/delete")


def test_portrait_upload_persists_and_renders():
    name = "Plan-Test Portrait NPC"
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64  # minimal fake PNG bytes
    resp = client.post(
        "/npcs",
        data={"name": name, "disposition": "neutral"},
        files={"portrait": ("face.png", io.BytesIO(png), "image/png")},
    )
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        row = db.query(Npc).filter_by(name=name).first()
        assert row.portrait_path and row.portrait_path.startswith("portraits/")
        assert (config.MEDIA_DIR / row.portrait_path).is_file()
        stored = config.MEDIA_DIR / row.portrait_path
    finally:
        db.close()
    detail = client.get(f"/npcs/{_npc_id(name)}")
    assert f"/media/{row.portrait_path}" in detail.text
    client.post(f"/npcs/{_npc_id(name)}/delete")
    assert not stored.exists()  # file removed on delete


def test_portrait_rejects_disallowed_type():
    name = "Plan-Test Bad Portrait"
    resp = client.post(
        "/npcs",
        data={"name": name, "disposition": "neutral"},
        files={"portrait": ("evil.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert resp.status_code == 200
    assert "Unsupported image type" in resp.text
    assert _npc_id(name) is None  # not created


def test_roster_groups_null_and_dangling_faction_as_unaffiliated():
    client.post(
        "/npcs", data={"name": "Plan-Test No-Faction", "disposition": "neutral", "faction_id": ""}
    )
    # dangling: a faction_id that resolves to nothing
    client.post(
        "/npcs",
        data={"name": "Plan-Test Dangling", "disposition": "neutral", "faction_id": "888888"},
    )

    resp = client.get("/npcs")
    assert "Unaffiliated" in resp.text
    assert "Plan-Test No-Faction" in resp.text and "Plan-Test Dangling" in resp.text

    only_unaff = client.get("/npcs", params={"faction_id": "none"}, headers={"HX-Request": "true"})
    assert "Plan-Test No-Faction" in only_unaff.text
    assert "Plan-Test Dangling" in only_unaff.text

    for nm in ("Plan-Test No-Faction", "Plan-Test Dangling"):
        client.post(f"/npcs/{_npc_id(nm)}/delete")


def test_roster_filter_by_specific_faction():
    # Create a faction, then an NPC assigned to it; filtering by that id shows only that NPC.
    client.post("/factions", data={"name": "Plan-Test NPC Faction", "disposition": "neutral"})
    db = SessionLocal()
    try:
        from app.modules.factions.models import Faction

        fid = db.query(Faction).filter_by(name="Plan-Test NPC Faction").first().id
    finally:
        db.close()
    client.post(
        "/npcs", data={"name": "Plan-Test Member", "disposition": "neutral", "faction_id": str(fid)}
    )
    client.post(
        "/npcs", data={"name": "Plan-Test Outsider", "disposition": "neutral", "faction_id": ""}
    )

    filtered = client.get("/npcs", params={"faction_id": str(fid)}, headers={"HX-Request": "true"})
    assert "Plan-Test Member" in filtered.text
    assert "Plan-Test Outsider" not in filtered.text

    client.post(f"/npcs/{_npc_id('Plan-Test Member')}/delete")
    client.post(f"/npcs/{_npc_id('Plan-Test Outsider')}/delete")
    client.post(f"/factions/{fid}/delete")
