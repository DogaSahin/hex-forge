#!/usr/bin/env bash
set -euo pipefail
DEST="app/core/static/vendor"
mkdir -p "$DEST"
curl -fsSL "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js"                 -o "$DEST/htmx.min.js"
curl -fsSL "https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js"                 -o "$DEST/alpine.min.js"
curl -fsSL "https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"    -o "$DEST/sortable.min.js"
curl -fsSL "https://unpkg.com/konva@9.3.16/konva.min.js"                       -o "$DEST/konva.min.js"
echo "Vendored 4 libraries into $DEST"
