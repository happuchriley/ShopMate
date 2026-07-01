"""Low-level Telegram Bot API client."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _api_url(method: str) -> str:
    token = get_settings().telegram_bot_token
    return f"https://api.telegram.org/bot{token}/{method}"


async def send_text(
    chat_id: str,
    text: str,
    *,
    parse_mode: Optional[str] = None,
) -> dict:
    payload: dict = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(_api_url("sendMessage"), json=payload)
        response.raise_for_status()
        return response.json()


async def get_file_path(file_id: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(_api_url("getFile"), params={"file_id": file_id})
        response.raise_for_status()
        data = response.json()
        return data["result"]["file_path"]
