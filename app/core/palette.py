from __future__ import annotations

from app.core.registry import Registry


def palette_index(registry: Registry) -> list[dict]:
    entries = [{"label": n.label, "url": n.url} for n in registry.sorted_nav()]
    entries.append({"label": "Style reference", "url": "/style"})
    return entries


def search_index(registry: Registry, q: str) -> list[dict]:
    needle = q.strip().lower()
    entries = palette_index(registry)
    if not needle:
        return entries
    return [e for e in entries if needle in e["label"].lower()]
