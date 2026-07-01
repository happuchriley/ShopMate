"""Aiogram 3 Telegram bot with polling inside FastAPI lifespan."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_settings
from app.db.models import SessionLocal
from app.platforms import IncomingMessage, MessageType, Platform
from app.services import handler, knowledge

logger = logging.getLogger(__name__)

_bot: Optional[Bot] = None
_dispatcher: Optional[Dispatcher] = None
_polling_task: Optional[asyncio.Task] = None


def _default_business_id() -> str:
    return get_settings().default_business_id


async def _process_message(message: Message, message_type: MessageType, text: str | None, file_id: str | None) -> None:
    if not message.from_user:
        return
    user = message.from_user
    incoming = IncomingMessage(
        platform=Platform.TELEGRAM,
        platform_user_id=str(message.chat.id),
        business_id=_default_business_id(),
        message_type=message_type,
        text=text,
        media_url=file_id,
        display_name=user.full_name or user.username,
        raw={"message_id": message.message_id},
        message_id=str(message.message_id),
    )
    db = SessionLocal()
    try:
        await handler.handle_incoming(db, incoming)
    finally:
        db.close()


async def cmd_start(message: Message) -> None:
    profile = knowledge.load_business(_default_business_id())
    await message.answer(
        f"👋 Welcome to {profile.name}!\n"
        f"{profile.tagline}\n\n"
        "Ask about phones, prices, repairs, or send a photo.\n"
        "Reply HUMAN anytime to reach our team.\n"
        "Mo wo kasa — English anaa Twi!"
    )


async def on_text(message: Message) -> None:
    await _process_message(message, MessageType.TEXT, message.text, None)


async def on_photo(message: Message) -> None:
    if not message.photo:
        return
    photo = message.photo[-1]
    caption = message.caption
    await _process_message(message, MessageType.IMAGE, caption, photo.file_id)


def create_dispatcher() -> tuple[Bot, Dispatcher]:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(on_text, F.content_type == ContentType.TEXT)
    dp.message.register(on_photo, F.photo)

    return bot, dp


async def start_polling() -> None:
    global _bot, _dispatcher, _polling_task
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("Telegram token missing — polling not started")
        return

    _bot, _dispatcher = create_dispatcher()
    logger.info("Starting Telegram polling…")

    async def _poll() -> None:
        try:
            await _dispatcher.start_polling(_bot, handle_signals=False)
        except asyncio.CancelledError:
            logger.info("Telegram polling cancelled")
            raise
        except Exception as exc:
            logger.exception("Telegram polling error: %s", exc)

    _polling_task = asyncio.create_task(_poll())


async def stop_polling() -> None:
    global _bot, _dispatcher, _polling_task
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
        _polling_task = None
    if _bot:
        await _bot.session.close()
        _bot = None
    _dispatcher = None
    logger.info("Telegram polling stopped")
