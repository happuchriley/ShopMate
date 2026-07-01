"""OpenAI vision for product photo understanding."""

from __future__ import annotations

import base64
import logging

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.knowledge import BusinessProfile

logger = logging.getLogger(__name__)


async def analyze_product_photo(
    profile: BusinessProfile,
    image_bytes: bytes,
    *,
    mime_type: str = "image/jpeg",
    user_caption: str = "",
    language: str = "en",
) -> str:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    lang_note = "Reply in English." if language == "en" else "Reply in Twi when possible."
    prompt = f"""You are the assistant for {profile.name}, a phone shop in Ghana.
The customer sent a photo. Identify phones/accessories if visible, suggest matches from our catalog,
mention prices in GHS when relevant, and ask a helpful follow-up question.
{lang_note}
Customer caption: {user_caption or '(none)'}

Our catalog summary:
{profile.knowledge_context()}
"""

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=400,
            temperature=0.3,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.exception("Vision analysis failed: %s", exc)
        if language == "twi":
            return "Metumi nnhu mfonini no yiye. Fa phone no din anaa HUMAN kyerɛ."
        return "I couldn't analyze that photo clearly. Tell me the phone model or reply HUMAN for help."
