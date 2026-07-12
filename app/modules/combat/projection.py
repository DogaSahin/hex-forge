from __future__ import annotations


def hp_band(current: int, maximum: int) -> str:
    """Coarse health band for HP bars. On the player screen this band is the ONLY
    HP signal shown (no numbers), so both surfaces must agree on the thresholds."""
    ratio = (current / maximum) if maximum > 0 else 0
    if ratio <= 0.25:
        return "low"
    if ratio <= 0.5:
        return "mid"
    return "high"
