"""OpenAI text generation for ShopMate."""

from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.knowledge import BusinessProfile

logger = logging.getLogger(__name__)


def _client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _system_prompt(profile: BusinessProfile, language: str, customer_context: str) -> str:
    lang_note = "Respond in English." if language == "en" else "Respond in Twi (Akan) when possible, English if unsure."
    return f"""You are ShopMate, the friendly AI assistant for {profile.name}.
{profile.tagline}

Use ONLY the business knowledge below. If you don't know, say you'll connect the customer with staff.
Keep replies concise and helpful for chat (WhatsApp/Telegram).
Capture buying intent and suggest visiting the shop or leaving contact details.
If the customer asks for a person, tell them to reply HUMAN.
{lang_note}

Business knowledge:
{profile.knowledge_context()}

Customer context:
{customer_context}
"""


async def generate_reply(
    profile: BusinessProfile,
    user_message: str,
    *,
    language: str = "en",
    customer_context: str = "",
    conversation_history: Optional[list[dict[str, str]]] = None,
) -> str:
    settings = get_settings()
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _system_prompt(profile, language, customer_context)},
    ]
    if conversation_history:
        messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": user_message})

    try:
        response = await _client().chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=500,
            temperature=0.4,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.exception("OpenAI text generation failed: %s", exc)
        if language == "twi":
            return "Kafra, mfomso bi aba. Bɔ HUMAN na wo ne yɛn staff nkasa."
        return "Sorry, I'm having trouble right now. Reply HUMAN to reach our team."
