"""Vite asset tags for Jinja templates.

Emits either the Vite dev-server (HMR) script tags or the built-manifest tags,
based on ``config.VITE_DEV``. When no build exists yet (prod mode, missing
manifest) it degrades to an HTML comment so pages still render — the Python test
suite and a not-yet-built checkout stay usable; CI builds before serving.
"""

from __future__ import annotations

import json

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.core import config


def _dev_tags() -> Markup:
    base = config.VITE_DEV_SERVER_URL.rstrip("/")
    return Markup(
        f'<script type="module" src="{base}/@vite/client"></script>\n'
        f'<script type="module" src="{base}/{config.VITE_ENTRY}"></script>'
    )


def _prod_tags() -> Markup:
    manifest_path = config.VITE_DIST_DIR / ".vite" / "manifest.json"
    if not manifest_path.exists():
        return Markup("<!-- vite assets not built (run `npm run build`) -->")
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    entry = manifest[config.VITE_ENTRY]  # KeyError = a real manifest/config mismatch
    tags = [f'<link rel="stylesheet" href="/static/dist/{css}">' for css in entry.get("css", [])]
    tags.append(f'<script type="module" src="/static/dist/{entry["file"]}"></script>')
    return Markup("\n".join(tags))


def vite_entry() -> Markup:
    """The <script>/<link> tags for the island entry, dev- or prod-appropriate."""
    return _dev_tags() if config.VITE_DEV else _prod_tags()


def register_vite_globals(templates: Jinja2Templates) -> None:
    """Register ``vite_entry`` as a Jinja global on a templates environment."""
    templates.env.globals["vite_entry"] = vite_entry
