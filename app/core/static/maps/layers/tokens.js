function tokenNode(t, gridSize) {
  const px = (t.size || 1) * gridSize;
  const group = new Konva.Group({ x: t.x, y: t.y, draggable: true, id: `tok-${t.id}` });
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
  if (t.name) {
    group.add(new Konva.Text({ text: t.name, y: px + 2, fontSize: 13, fill: "#eee",
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
      layer.draw();
      if (api.onLayerReady) api.onLayerReady(layer, gridSize);
    },
    update(delta) {
      // token.move delta: { token_id, x, y }
      const node = layer.findOne(`#tok-${delta.token_id}`);
      if (node) { node.position({ x: delta.x, y: delta.y }); layer.draw(); }
    },
    destroy() { layer.destroy(); },
  };
  return api;
}
