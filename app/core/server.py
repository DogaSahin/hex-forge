from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

CORE_DIR = Path(__file__).resolve().parent
STATIC_DIR = CORE_DIR / "static"
TEMPLATES_DIR = CORE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app() -> FastAPI:
    app = FastAPI(title="Hexforge")

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/smoke", response_class=HTMLResponse)
    def smoke(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "smoke.html", {"count_start": 0})

    @app.get("/smoke/fragment", response_class=HTMLResponse)
    def smoke_fragment() -> HTMLResponse:
        return HTMLResponse("<p id='swapped'>Swapped by HTMX ✔</p>")

    return app
