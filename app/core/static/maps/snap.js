export function snapToGrid(x, y, size, offX, offY) {
  if (!size || size <= 0) return { x, y };
  return {
    x: Math.round((x - offX) / size) * size + offX,
    y: Math.round((y - offY) / size) * size + offY,
  };
}
