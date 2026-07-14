// HP band colours mirror app.css (--danger/--warning/--success) and the shared
// band semantics in app/core/projection.py::hp_band — low/mid/high must always
// agree with the server so DM and player bars never disagree on colour.
const BAND_COLORS = { low: "#d15b5b", mid: "#e0a54a", high: "#5aa46a" };

function computeBand(current, max) {
  if (!max || max <= 0) return null;
  const ratio = (current || 0) / max;
  if (ratio <= 0.25) return "low";
  if (ratio <= 0.5) return "mid";
  return "high";
}

function hpBandFor(t) {
  // Player surface ships a precomputed hp_band (the only HP signal players ever
  // get). DM surface ships numeric hp_current/hp_max instead — derive the same
  // band client-side so both surfaces render an identical bar.
  if (t.hp_band) return t.hp_band;
  if (t.hp_max != null) return computeBand(t.hp_current, t.hp_max);
  return null;
}

function tokenNode(t, gridSize) {
  const px = (t.size || 1) * gridSize;
  const group = new Konva.Group({ x: t.x, y: t.y, draggable: false, id: `tok-${t.id}` });
  group.setAttr("tokenId", t.id);
  if (t.kind === "image" && t.image_path) {
    const img = new Image();
    img.onload = () => { shape.image(img); group.getLayer() && group.getLayer().draw(); };
    img.src = `/media/${t.image_path}`;
    const shape = new Konva.Image({ image: null, width: px, height: px });
    group.add(shape);
  } else {
    group.add(new Konva.Circle({ radius: px / 2, x: px / 2, y: px / 2,
      fill: t.color || "#888", stroke: "rgba(0,0,0,0.5)", strokeWidth: 2 }));
  }
  let belowTokenY = px + 2;
  const band = hpBandFor(t);
  if (band) {
    const barHeight = 4;
    group.add(new Konva.Rect({ x: 0, y: belowTokenY, width: px, height: barHeight,
      fill: "rgba(0,0,0,0.4)", cornerRadius: 2 }));
    group.add(new Konva.Rect({ x: 0, y: belowTokenY, width: px, height: barHeight,
      fill: BAND_COLORS[band] || BAND_COLORS.high, cornerRadius: 2 }));
    belowTokenY += barHeight + 2;
  }
  if (t.name) {
    group.add(new Konva.Text({ text: t.name, y: belowTokenY, fontSize: 13, fill: "#eee",
      width: px, align: "center" }));
  }
  if (t.visible_to_players === false || t.layer === "dm") {
    group.opacity(0.55);
  }
  return group;
}

export function createTokensLayer(ctx) {
  const layer = new Konva.Layer();
  let gridSize = 70;
  const api = {
    konvaLayer: layer,
    render(state) {
      layer.destroyChildren();
      gridSize = (state.map && state.map.grid_size_px) || 70;
      (state.tokens || []).forEach((t) => layer.add(tokenNode(t, gridSize)));
      // Read-only surfaces (player) must not even hit-test tokens: no drag, no
      // dblclick-to-menu. Tokens are recreated every render(), so this must be
      // re-applied here rather than set once at layer creation.
      layer.listening(ctx.mode === "dm");
      layer.draw();
      if (api.onLayerReady) api.onLayerReady(layer, gridSize);
    },
    update(delta) {
      // token.move delta: { token_id, x, y }
      const node = layer.findOne(`#tok-${delta.token_id}`);
      if (node) { node.position({ x: delta.x, y: delta.y }); layer.draw(); }
    },
    setDraggable(draggable) {
      // Applies to all token Groups currently on the layer. Tokens are recreated on every
      // render(), so callers must re-apply this after each render()/refresh(). DM-mode-only
      // caller (map.js); the player surface never calls this, and the layer isn't even
      // listening there, so tokens stay inert regardless.
      layer.getChildren().forEach((group) => group.draggable(!!draggable));
    },
    destroy() { layer.destroy(); },
  };
  return api;
}
