#!/usr/bin/env python3
"""Print Telegram chat ID when owner sends /start to the bot."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message


async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def on_start(message: Message) -> None:
        chat_id = message.chat.id
        name = message.from_user.full_name if message.from_user else "Unknown"
        print(f"\n✅ Owner chat ID: {chat_id}")
        print(f"   Name: {name}")
        print(f"\nAdd to businesses/*/config.yaml:")
        print(f'   owner_telegram_chat_id: "{chat_id}"')
        await message.answer(
            f"Your chat ID is `{chat_id}`\n\n"
            "Add this to your business config.yaml as owner_telegram_chat_id.",
            parse_mode="Markdown",
        )

    print("Send /start to your bot on Telegram to get your owner chat ID…")
    print("Press Ctrl+C to stop.\n")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
