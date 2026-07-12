import { LAYER_FACTORIES } from "./layers/index.js";

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
    stage.size({ width: state.map.image_w || 1200, height: state.map.image_h || 800 });
    layers.forEach((l) => l.inst.render(state));
  }
  refresh();

  // WS wiring is added in Slice 6; expose the layer table for those tasks.
  host._hexLayers = layers;
  host._hexRefresh = refresh;
}
