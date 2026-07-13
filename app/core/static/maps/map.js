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

    tokensLayer.inst.konvaLayer.on("dblclick dbltap", (e) => {
      if (host.dataset.tool === "measure") return; // ruler owns dblclick while measuring
      const group = e.target.getAttr("tokenId") ? e.target : e.target.findAncestor("Group");
      const tid = group && group.getAttr("tokenId");
      if (tid && window.htmx) {
        htmx.ajax("GET", `/token/${tid}/menu`, { target: "#token-menu-host", swap: "innerHTML" });
      }
    });
  }

  const rulerLayer = layers.find((l) => l.name === "ruler");
  if (rulerLayer && mode === "dm") {
    let measuring = false;
    stage.on("mousedown touchstart", () => {
      if (host.dataset.tool !== "measure") return;
      const p = stage.getPointerPosition();
      if (!p) return;
      rulerLayer.inst.setMeta((host._lastState || {}).map || {});
      if (!measuring) {
        rulerLayer.inst.beginAt([p.x, p.y]);
        measuring = true;
      } else {
        rulerLayer.inst.addWaypoint([p.x, p.y]);
      }
    });
    stage.on("mousemove touchmove", () => {
      if (!measuring || host.dataset.tool !== "measure") return;
      const p = stage.getPointerPosition();
      if (p) rulerLayer.inst.moveTo([p.x, p.y]);
    });
    stage.on("dblclick dbltap", () => {
      if (host.dataset.tool === "measure" && measuring) {
        rulerLayer.inst.end();
        measuring = false;
      }
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && measuring) {
        rulerLayer.inst.end();
        measuring = false;
      }
    });

    // Reset the ruler when the DM switches away from the measure tool.
    const toolObserver = new MutationObserver(() => {
      if (host.dataset.tool !== "measure" && measuring) {
        rulerLayer.inst.end();
        measuring = false;
      }
    });
    toolObserver.observe(host, { attributes: true, attributeFilter: ["data-tool"] });
  }

  if (mode === "dm") {
    // Rectangle reveal/hide
    let fogStart = null;
    stage.on("mousedown touchstart", () => {
      const tool = host.dataset.tool;
      if (tool !== "reveal-rect" && tool !== "hide") return;
      const p = stage.getPointerPosition();
      if (!p) return;
      fogStart = [p.x, p.y];
    });
    stage.on("mouseup touchend", async () => {
      const tool = host.dataset.tool;
      if ((tool !== "reveal-rect" && tool !== "hide") || !fogStart) return;
      const p = stage.getPointerPosition();
      if (!p) {
        fogStart = null;
        return;
      }
      const x = Math.min(fogStart[0], p.x);
      const y = Math.min(fogStart[1], p.y);
      const w = Math.abs(p.x - fogStart[0]);
      const h = Math.abs(p.y - fogStart[1]);
      fogStart = null;
      if (w < 3 || h < 3) return;
      const op = tool === "hide" ? "hide" : "reveal";
      const geom = JSON.stringify({
        type: "rect",
        x: Math.round(x),
        y: Math.round(y),
        w: Math.round(w),
        h: Math.round(h),
      });
      await fetch(`/map/${mapId}/fog`, { method: "POST", body: new URLSearchParams({ op, geom }) });
      refresh();
    });

    // Freehand brush reveal
    let brushPts = null;
    stage.on("mousedown touchstart", () => {
      if (host.dataset.tool !== "reveal-brush") return;
      const p = stage.getPointerPosition();
      if (!p) return;
      brushPts = [p.x, p.y];
    });
    stage.on("mousemove touchmove", () => {
      if (host.dataset.tool !== "reveal-brush" || !brushPts) return;
      const p = stage.getPointerPosition();
      if (!p) return;
      brushPts.push(p.x, p.y);
    });
    stage.on("mouseup touchend", async () => {
      if (host.dataset.tool !== "reveal-brush" || !brushPts) return;
      const pts = brushPts;
      brushPts = null;
      if (pts.length < 6) return;
      const geom = JSON.stringify({ type: "path", points: pts.map((n) => Math.round(n)) });
      await fetch(`/map/${mapId}/fog`, {
        method: "POST",
        body: new URLSearchParams({ op: "reveal", geom }),
      });
      refresh();
    });
  }

  // WS wiring is added in Slice 6; expose the layer table for those tasks.
  host._hexLayers = layers;
  host._hexRefresh = refresh;
}
