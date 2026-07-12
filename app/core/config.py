from __future__ import annotations

import os
from pathlib import Path

# hex-forge/app/core/config.py -> parents: core, app, hex-forge
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
MAPS_DIR = MEDIA_DIR / "maps"
TOKENS_DIR = MEDIA_DIR / "tokens"
PORTRAITS_DIR = MEDIA_DIR / "portraits"

DB_PATH = DATA_DIR / "hexforge.db"
DB_URL = os.environ.get("HEXFORGE_DB_URL", f"sqlite:///{DB_PATH.as_posix()}")

HOST = os.environ.get("HEXFORGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("HEXFORGE_PORT", "8000"))

# Populated from Epic 1 onward as modules are enabled.
ENABLED_MODULES: list[str] = [
    "app.modules._demo",
    "app.modules.dice",
    "app.modules.factions",
    "app.modules.npcs",
    "app.modules.wiki",
    "app.modules.combat",
]

# Grid defaults (spec §6.2).
DEFAULT_GRID_SIZE_PX = 70
DEFAULT_FEET_PER_SQUARE = 5


def _ensure_dirs() -> None:
    for directory in (DATA_DIR, MEDIA_DIR, MAPS_DIR, TOKENS_DIR, PORTRAITS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


_ensure_dirs()
