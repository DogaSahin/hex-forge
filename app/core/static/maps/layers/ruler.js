// app/core/static/maps/layers/ruler.js
// DM-only measuring layer. Mirrors app/modules/maps/distance.py term-for-term so the
// client-side live label always agrees with any server-computed distance for the same
// map meta (grid_size_px / feet_per_square / diagonal_rule).

function segmentFeet(dx, dy, feet, rule) {
  dx = Math.abs(dx);
  dy = Math.abs(dy);
  const hi = Math.max(dx, dy);
  const lo = Math.min(dx, dy);
  if (rule === "chebyshev") return hi * feet;
  if (rule === "five_ten_five") return (hi + Math.floor(lo / 2)) * feet;
  if (rule === "euclidean") return Math.round(Math.hypot(dx, dy)) * feet;
  if (rule === "manhattan") return (dx + dy) * feet;
  return hi * feet; // unknown rule -> default to chebyshev
}

const DEFAULT_META = { grid_size_px: 70, feet_per_square: 5, diagonal_rule: "chebyshev" };

export function createRulerLayer(ctx) {
  const layer = new Konva.Layer({ listening: false });
  let pts = []; // committed waypoints, px pairs [x, y]
  let cursor = null; // live endpoint, px pair, or null when not measuring
  let mapMeta = { ...DEFAULT_META };

  function totalFeet(all) {
    const g = mapMeta.grid_size_px || DEFAULT_META.grid_size_px;
    const feet = mapMeta.feet_per_square || DEFAULT_META.feet_per_square;
    const rule = mapMeta.diagonal_rule || DEFAULT_META.diagonal_rule;
    let sum = 0;
    for (let i = 1; i < all.length; i++) {
      const dx = Math.round(Math.abs(all[i][0] - all[i - 1][0]) / g);
      const dy = Math.round(Math.abs(all[i][1] - all[i - 1][1]) / g);
      sum += segmentFeet(dx, dy, feet, rule);
    }
    return sum;
  }

  function redraw() {
    layer.destroyChildren();
    const all = cursor ? [...pts, cursor] : pts;
    if (all.length >= 2) {
      layer.add(
        new Konva.Line({
          points: all.flat(),
          stroke: "#f0a500",
          strokeWidth: 2,
          dash: [8, 6],
          listening: false,
        })
      );
      const [lx, ly] = all[all.length - 1];
      const label = new Konva.Label({ x: lx + 8, y: ly + 8, listening: false });
      label.add(new Konva.Tag({ fill: "rgba(0,0,0,0.75)" }));
      label.add(
        new Konva.Text({
          text: `${totalFeet(all)} ft`,
          padding: 4,
          fill: "#f0a500",
          fontSize: 14,
        })
      );
      layer.add(label);
    }
    layer.draw();
  }

  return {
    konvaLayer: layer,
    render(state) {
      if (state && state.map) mapMeta = state.map;
    },
    update() {},
    destroy() {
      layer.destroy();
    },
    // Ruler-specific API (not part of the uniform layer contract):
    setMeta(map) {
      mapMeta = map && Object.keys(map).length ? map : { ...DEFAULT_META };
    },
    beginAt(pt) {
      pts = [pt];
      cursor = pt;
      redraw();
    },
    addWaypoint(pt) {
      pts.push(pt);
      redraw();
    },
    moveTo(pt) {
      cursor = pt;
      redraw();
    },
    end() {
      pts = [];
      cursor = null;
      redraw();
    },
  };
}
