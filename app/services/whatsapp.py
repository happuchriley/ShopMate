"""WhatsApp Cloud API webhook and messaging."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.platforms import IncomingMessage, MessageType, Platform

logger = logging.getLogger(__name__)


def verify_signature(payload: bytes, signature_header: str | None) -> bool:
    """Verify X-Hub-Signature-256 from Meta webhook."""
    settings = get_settings()
    secret = settings.whatsapp_app_secret
    if not secret:
        logger.warning("WHATSAPP_APP_SECRET not set — skipping signature verification")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1]
    computed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected)


def parse_webhook(body: dict[str, Any], default_business_id: str) -> list[IncomingMessage]:
    messages: list[IncomingMessage] = []
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                wa_id = msg.get("from", "")
                msg_type = msg.get("type", "text")
                text = None
                media_id = None
                mime_type = None

                if msg_type == "text":
                    text = msg.get("text", {}).get("body")
                    mtype = MessageType.TEXT
                elif msg_type == "image":
                    mtype = MessageType.IMAGE
                    image = msg.get("image", {})
                    media_id = image.get("id")
                    text = image.get("caption")
                    mime_type = image.get("mime_type", "image/jpeg")
                else:
                    mtype = MessageType.UNKNOWN

                messages.append(
                    IncomingMessage(
                        platform=Platform.WHATSAPP,
                        platform_user_id=wa_id,
                        business_id=default_business_id,
                        message_type=mtype,
                        text=text,
                        media_url=media_id,
                        media_mime_type=mime_type,
                        raw=msg,
                        message_id=msg.get("id"),
                    )
                )
    return messages


async def download_media(media_id: str) -> tuple[bytes, str]:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    base = f"https://graph.facebook.com/{settings.whatsapp_api_version}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        meta = await client.get(f"{base}/{media_id}", headers=headers)
        meta.raise_for_status()
        url = meta.json().get("url")
        mime = meta.json().get("mime_type", "image/jpeg")
        if not url:
            raise ValueError("No media URL in WhatsApp response")
        media = await client.get(url, headers=headers)
        media.raise_for_status()
        return media.content, mime


async def send_text(to: str, text: str) -> dict:
    settings = get_settings()
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        raise RuntimeError("WhatsApp credentials not configured")

    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
