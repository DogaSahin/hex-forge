from __future__ import annotations

import io
import uuid

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core import config

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_MAP_BYTES = 25 * 1024 * 1024
MAX_TOKEN_BYTES = 5 * 1024 * 1024


def _store_image(upload: UploadFile | None, subdir: str, dest_dir, max_bytes: int):
    """Validate + persist an image. Returns (rel_path, width, height, error)."""
    if upload is None or not upload.filename:
        return None, None, None, None
    ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return None, None, None, "Unsupported image type."
    data = upload.file.read()
    if not data:
        return None, None, None, None
    if len(data) > max_bytes:
        return None, None, None, "Image too large."
    try:
        with Image.open(io.BytesIO(data)) as im:
            width, height = im.size
    except (UnidentifiedImageError, OSError):
        return None, None, None, "Unreadable image."
    fname = f"{uuid.uuid4().hex}.{ext}"
    (dest_dir / fname).write_bytes(data)
    return f"{subdir}/{fname}", width, height, None


def store_map_image(upload: UploadFile | None):
    return _store_image(upload, "maps", config.MAPS_DIR, MAX_MAP_BYTES)


def store_token_image(upload: UploadFile | None):
    return _store_image(upload, "tokens", config.TOKENS_DIR, MAX_TOKEN_BYTES)
