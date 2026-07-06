from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

CORE_DIR = Path(__file__).resolve().parent
STATIC_DIR = CORE_DIR / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Hexforge")

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
