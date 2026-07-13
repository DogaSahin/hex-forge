// app/core/static/maps/layers/fog.js
// Base map state is fully fogged; each op punches a hole (reveal) or re-fogs (hide).
// Two-surface: DM sees fog at ~50% opacity (can see the whole map while knowing
// what's hidden); the player sees it fully opaque.
export function createFogLayer(ctx) {
  const layer = new Konva.Layer({ listening: false });
  const opaque = ctx.mode === "player";
  return {
    konvaLayer: layer,
    render(state) {
      layer.destroyChildren();
      const m = state.map || {};
      const w = m.image_w || ctx.stage.width();
      const h = m.image_h || ctx.stage.height();
      const ops = state.fog || [];
      // Base: full fog rectangle.
      const fog = new Konva.Rect({ x: 0, y: 0, width: w, height: h, fill: "#0a0a0f" });
      layer.add(fog);
      // Punch/repaint via globalCompositeOperation on the same layer.
      ops.forEach((entry) => {
        const g = entry.geom;
        const comp = entry.op === "reveal" ? "destination-out" : "source-over";
        if (g.type === "all") {
          layer.add(
            new Konva.Rect({
              x: 0,
              y: 0,
              width: w,
              height: h,
              fill: "#0a0a0f",
              globalCompositeOperation: comp,
            })
          );
        } else if (g.type === "rect") {
          layer.add(
            new Konva.Rect({
              x: g.x,
              y: g.y,
              width: g.w,
              height: g.h,
              fill: "#0a0a0f",
              globalCompositeOperation: comp,
            })
          );
        } else if (g.type === "path") {
          layer.add(
            new Konva.Line({
              points: g.points,
              closed: true,
              fill: "#0a0a0f",
              globalCompositeOperation: comp,
            })
          );
        }
      });
      layer.opacity(opaque ? 1.0 : 0.5);
      layer.draw();
    },
    update() {},
    destroy() {
      layer.destroy();
    },
  };
}
