// Internal render-layer registry (kept private to the map module — no core API yet).
import { createBackgroundLayer } from "./background.js";
import { createGridLayer } from "./grid.js";

// Ordered bottom -> top. grid/tokens/fog/dm/ruler appended in later tasks.
export const LAYER_FACTORIES = [
  { name: "background", make: createBackgroundLayer, modes: ["dm", "player"] },
  { name: "grid", make: createGridLayer, modes: ["dm", "player"] },
];
