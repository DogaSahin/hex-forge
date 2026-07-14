export function createBackgroundLayer(ctx) {
  const layer = new Konva.Layer({ listening: false });
  return {
    konvaLayer: layer,
    render(state) {
      layer.destroyChildren();
      const m = state.map;
      if (!m || !m.image_path) {
        layer.draw();
        return;
      }
      const img = new Image();
      img.onload = () => {
        layer.add(new Konva.Image({ image: img, x: 0, y: 0, width: m.image_w, height: m.image_h }));
        layer.draw();
      };
      img.src = `/media/${m.image_path}`;
    },
    update() {},
    destroy() {
      layer.destroy();
    },
  };
}
