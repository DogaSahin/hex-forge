from __future__ import annotations


def snap_to_grid(x: int, y: int, size: int, off_x: int, off_y: int) -> tuple[int, int]:
    """Nearest grid intersection. size<=0 => snapping disabled (return input)."""
    if size <= 0:
        return x, y
    sx = round((x - off_x) / size) * size + off_x
    sy = round((y - off_y) / size) * size + off_y
    return int(sx), int(sy)
