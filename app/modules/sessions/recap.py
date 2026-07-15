from __future__ import annotations

from collections.abc import Iterable

# Fixed output order. Untagged ("none") lines are deliberately absent: the recap is
# the story of the session, and an untagged line is a scratch note.
TAG_HEADINGS: list[tuple[str, str]] = [
    ("combat", "Combat"),
    ("roleplay", "Roleplay"),
    ("loot", "Loot"),
    ("thread", "Threads"),
]


def compile_recap(logs: Iterable, tags: set[str] | None = None) -> str:
    """Concatenate tagged log lines into grouped markdown.

    Pure: takes anything with .tag/.text/.logged_at/.id, returns a string. No DB.
    """
    selected = {tag for tag, _ in TAG_HEADINGS} if not tags else set(tags)
    ordered = sorted(logs, key=lambda log: (log.logged_at, log.id))

    parts: list[str] = []
    for tag, heading in TAG_HEADINGS:
        if tag not in selected:
            continue
        lines = [log for log in ordered if log.tag == tag]
        if not lines:
            continue
        parts.append(f"## {heading}")
        parts.extend(f"- {log.text}" for log in lines)
        parts.append("")
    return "\n".join(parts).strip()
