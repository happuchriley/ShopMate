"""Media download and processing utilities."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.services.media_types import extension_for_mime

logger = logging.getLogger(__name__)


async def download_url(url: str, headers: Optional[dict[str, str]] = None) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, headers=headers or {})
        response.raise_for_status()
        return response.content


async def download_telegram_file(bot_token: str, file_path: str) -> bytes:
    url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    return await download_url(url)


def describe_image_bytes(data: bytes, mime_type: str | None = None) -> dict:
    ext = extension_for_mime(mime_type)
    return {"bytes": data, "mime_type": mime_type or "image/jpeg", "extension": ext}
