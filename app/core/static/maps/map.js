import { LAYER_FACTORIES } from "./layers/index.js";
import { snapToGrid } from "./snap.js";

export function mountEditor(host) {
  if (!host || host.dataset.mounted) return;
  host.dataset.mounted = "1";
  const mapId = host.dataset.mapId;
  const mode = host.dataset.mode || "dm";

  const stage = new Konva.Stage({ container: host, width: host.clientWidth || 1200, height: 800 });
  const ctx = { stage, mode, mapId };
  const layers = LAYER_FACTORIES
    .filter((f) => f.modes.includes(mode))
    .map((f) => ({ name: f.name, inst: f.make(ctx) }));
  layers.forEach((l) => stage.add(l.inst.konvaLayer));

  const stateUrl = mode === "player" ? `/map/${mapId}/player-state` : `/map/${mapId}/state`;
  async function refresh() {
    const state = await fetch(stateUrl).then((r) => r.json());
    if (!state.map) return;
    host._lastState = state;
    stage.size({ width: state.map.image_w || 1200, height: state.map.image_h || 800 });
    layers.forEach((l) => l.inst.render(state));
  }
  refresh();
  host.addEventListener("map:refresh", refresh);

  const tokensLayer = layers.find((l) => l.name === "tokens");
  if (tokensLayer && mode === "dm") {
    tokensLayer.inst.konvaLayer.on("dragend", async (e) => {
      // Only token Groups are draggable, so e.target is normally the Group itself;
      // fall back to the ancestor Group if a child shape ever becomes the target.
      const group = e.target.getAttr("tokenId") ? e.target : e.target.findAncestor("Group");
      const tid = group && group.getAttr("tokenId");
      if (!tid) return;
      const st = host._lastState || {};
      const m = st.map || {};
      let { x, y } = group.position();
      if (host.dataset.snap === "true") {
        const s = snapToGrid(x, y, m.grid_size_px, m.grid_offset_x, m.grid_offset_y);
        x = s.x;
        y = s.y;
        group.position({ x, y });
        group.getLayer().draw();
      }
      const body = new URLSearchParams({ x: Math.round(x), y: Math.round(y), snap: host.dataset.snap === "true" ? "1" : "" });
      await fetch(`/token/${tid}/move`, { method: "POST", body });
    });
  }

  // WS wiring is added in Slice 6; expose the layer table for those tasks.
  host._hexLayers = layers;
  host._hexRefresh = refresh;
}
