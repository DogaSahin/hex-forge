from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Hexforge")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
