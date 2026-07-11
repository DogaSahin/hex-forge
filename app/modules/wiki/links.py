from __future__ import annotations

import html
import re
from collections.abc import Callable

import markdown

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
# Splits text into non-code / code segments; code segments are the odd indices.
_CODE_SPLIT_RE = re.compile(r"(```.*?```|`[^`]*`)", re.DOTALL)


def slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", (text or "").strip().lower()).strip("-")
    return slug or "page"


def _non_code_segments(text: str) -> list[str]:
    return _CODE_SPLIT_RE.split(text)


def extract_wikilinks(body_md: str | None) -> list[str]:
    """Distinct [[names]] in document order, skipping fenced/inline code."""
    parts = _non_code_segments(body_md or "")
    names: list[str] = []
    seen: set[str] = set()
    for i in range(0, len(parts), 2):  # even indices are outside code
        for match in _WIKILINK_RE.finditer(parts[i]):
            name = match.group(1).strip()
            key = name.lower()
            if name and key not in seen:
                seen.add(key)
                names.append(name)
    return names


def render_markdown(body_md: str | None, resolve_href: Callable[[str], tuple[str, bool]]) -> str:
    """Render markdown to HTML, rewriting [[Name]] (outside code) into anchors."""
    text = body_md or ""
    tokens: dict[str, str] = {}

    def _stash(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        token = f"\x00WL{len(tokens)}\x00"
        tokens[token] = name
        return token

    parts = _non_code_segments(text)
    for i in range(0, len(parts), 2):
        parts[i] = _WIKILINK_RE.sub(_stash, parts[i])
    rendered = markdown.markdown("".join(parts), extensions=["fenced_code", "tables"])
    for token, name in tokens.items():
        rendered = rendered.replace(token, _anchor(name, resolve_href))
    return rendered


def _anchor(name: str, resolve_href: Callable[[str], tuple[str, bool]]) -> str:
    href, resolved = resolve_href(name)
    cls = "wikilink" if resolved else "wikilink wikilink-new"
    return f'<a class="{cls}" href="{html.escape(href, quote=True)}">{html.escape(name)}</a>'
