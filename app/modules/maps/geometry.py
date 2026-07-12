from __future__ import annotations

import math


def snap_to_grid(x: int, y: int, size: int, off_x: int, off_y: int) -> tuple[int, int]:
    """Nearest grid intersection. size<=0 => snapping disabled (return input).

    Uses half-up rounding (``floor(v + 0.5)``) rather than Python's banker's
    ``round`` so the result is byte-for-byte identical to the client mirror's
    ``Math.round`` (snap.js). The whole point of the twin implementation is that
    the coordinate the DM sees snapped locally is the coordinate the server
    persists — banker's rounding would disagree with JS on exact half-cell inputs
    (e.g. x=35, size=70) and desync by one grid cell.
    """
    if size <= 0:
        return x, y
    sx = math.floor((x - off_x) / size + 0.5) * size + off_x
    sy = math.floor((y - off_y) / size + 0.5) * size + off_y
    return int(sx), int(sy)
