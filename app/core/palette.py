from __future__ import annotations

from app.core.registry import Registry


def palette_index(registry: Registry, jump_targets: list[dict] | None = None) -> list[dict]:
    entries = [{"label": n.label, "url": n.url} for n in registry.sorted_nav()]
    entries.append({"label": "Style reference", "url": "/style"})
    if jump_targets:
        entries.extend({"label": t["label"], "url": t["url"]} for t in jump_targets)
    return entries


def search_index(registry: Registry, q: str, jump_targets: list[dict] | None = None) -> list[dict]:
    needle = q.strip().lower()
    entries = palette_index(registry, jump_targets)
    if not needle:
        return entries
    return [e for e in entries if needle in e["label"].lower()]
