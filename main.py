from __future__ import annotations

import uvicorn

from app.core.config import HOST, PORT
from app.core.server import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
