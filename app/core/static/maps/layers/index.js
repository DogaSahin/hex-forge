// Internal render-layer registry (kept private to the map module — no core API yet).
import { createBackgroundLayer } from "./background.js";
import { createGridLayer } from "./grid.js";
import { createTokensLayer } from "./tokens.js";
import { createFogLayer } from "./fog.js";
import { createRulerLayer } from "./ruler.js";

// Ordered bottom -> top. ruler must stay topmost —
// append any future layer above this comment, not below it.
export const LAYER_FACTORIES = [
  { name: "background", make: createBackgroundLayer, modes: ["dm", "player"] },
  { name: "grid", make: createGridLayer, modes: ["dm", "player"] },
  { name: "tokens", make: createTokensLayer, modes: ["dm", "player"] },
  { name: "fog", make: createFogLayer, modes: ["dm", "player"] },
  { name: "ruler", make: createRulerLayer, modes: ["dm"] },
];
