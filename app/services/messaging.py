"""Unified outbound messaging across platforms."""

from __future__ import annotations

import logging

from app.platforms import OutgoingMessage, Platform
from app.services import telegram_client, whatsapp

logger = logging.getLogger(__name__)


async def send_message(msg: OutgoingMessage) -> bool:
    try:
        if msg.platform == Platform.TELEGRAM:
            await telegram_client.send_text(
                chat_id=msg.platform_user_id,
                text=msg.text,
                parse_mode=msg.parse_mode,
            )
            return True
        if msg.platform == Platform.WHATSAPP:
            await whatsapp.send_text(
                to=msg.platform_user_id,
                text=msg.text,
            )
            return True
    except Exception as exc:
        logger.exception("Failed to send message via %s: %s", msg.platform, exc)
    return False


async def notify_owner_telegram(chat_id: str, text: str) -> None:
    if not chat_id:
        return
    try:
        await telegram_client.send_text(chat_id=chat_id, text=text)
    except Exception as exc:
        logger.exception("Owner notification failed: %s", exc)
