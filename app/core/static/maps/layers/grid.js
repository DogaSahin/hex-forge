// app/core/static/maps/layers/grid.js
export function createGridLayer(ctx) {
  const layer = new Konva.Layer({ listening: false });
  return {
    konvaLayer: layer,
    render(state) {
      layer.destroyChildren();
      const m = state.map;
      if (!m || !m.grid_visible || !m.grid_size_px) { layer.draw(); return; }
      const w = m.image_w || ctx.stage.width();
      const h = m.image_h || ctx.stage.height();
      const s = m.grid_size_px;
      const ox = m.grid_offset_x % s;
      const oy = m.grid_offset_y % s;
      const stroke = "rgba(255,255,255,0.18)";
      for (let x = ox; x <= w; x += s) {
        layer.add(new Konva.Line({ points: [x, 0, x, h], stroke, strokeWidth: 1 }));
      }
      for (let y = oy; y <= h; y += s) {
        layer.add(new Konva.Line({ points: [0, y, w, y], stroke, strokeWidth: 1 }));
      }
      layer.draw();
    },
    update() {},
    destroy() { layer.destroy(); },
  };
}
