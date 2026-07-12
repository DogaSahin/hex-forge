from fastapi.testclient import TestClient

from app.core.server import create_app

client = TestClient(create_app())


def test_palette_jumps_to_page_npc_faction():
    client.post("/wiki", data={"title": "Palette Wiki Zeta", "body_md": "x"})
    client.post("/npcs", data={"name": "Palette Npc Zeta", "disposition": "neutral"})
    client.post("/factions", data={"name": "Palette Faction Zeta", "disposition": "neutral"})

    page = client.get("/palette/search", params={"q": "Palette Wiki Zeta"})
    assert "/wiki/palette-wiki-zeta" in page.text

    npc = client.get("/palette/search", params={"q": "Palette Npc Zeta"})
    assert "/npcs/" in npc.text

    fac = client.get("/palette/search", params={"q": "Palette Faction Zeta"})
    assert "/factions/" in fac.text

    # Nav items still present on an empty query.
    nav = client.get("/palette/search", params={"q": "Dice"})
    assert "/dice" in nav.text
