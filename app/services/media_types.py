"""Media type helpers."""

from __future__ import annotations

MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def extension_for_mime(mime_type: str | None) -> str:
    if not mime_type:
        return ".jpg"
    return MIME_EXTENSIONS.get(mime_type.lower(), ".jpg")


def is_image_mime(mime_type: str | None) -> bool:
    return bool(mime_type and mime_type.lower().startswith("image/"))
