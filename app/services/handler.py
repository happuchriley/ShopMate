"""Central inbound message handler."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ConversationState, MessageLog
from app.platforms import IncomingMessage, MessageType, OutgoingMessage, Platform
from app.services import ai, hours, knowledge, leads, media, messaging, personalization, vision
from app.services import whatsapp as wa_service

logger = logging.getLogger(__name__)


def _get_state(db: Session, msg: IncomingMessage) -> ConversationState:
    state = (
        db.query(ConversationState)
        .filter_by(
            business_id=msg.business_id,
            platform=msg.platform.value,
            platform_user_id=msg.platform_user_id,
        )
        .first()
    )
    if state:
        return state
    state = ConversationState(
        business_id=msg.business_id,
        platform=msg.platform.value,
        platform_user_id=msg.platform_user_id,
        state="bot",
    )
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def _log_message(db: Session, msg: IncomingMessage, direction: str, content: str) -> None:
    db.add(
        MessageLog(
            business_id=msg.business_id,
            platform=msg.platform.value,
            platform_user_id=msg.platform_user_id,
            direction=direction,
            message_type=msg.message_type.value,
            content=content[:4000] if content else None,
        )
    )
    db.commit()


async def _handle_human_handoff(
    db: Session,
    msg: IncomingMessage,
    profile: knowledge.BusinessProfile,
    customer,
) -> str:
    state = _get_state(db, msg)
    state.state = "human"
    state.updated_at = datetime.utcnow()
    db.commit()

    owner_chat = profile.owner_telegram_chat_id
    notify = (
        f"🙋 HUMAN handoff requested\n"
        f"Business: {profile.name}\n"
        f"Platform: {msg.platform.value}\n"
        f"User: {msg.platform_user_id}\n"
        f"Name: {customer.display_name or '—'}\n"
        f"Last message: {msg.text or '(photo)'}"
    )
    if owner_chat:
        await messaging.notify_owner_telegram(owner_chat, notify)

    lang = customer.language
    if lang == "twi":
        return "Wɔde wo akɔma kɔ yɛn staff nkyɛn. Wobɛgye nkrato bi ntɛm."
    return "I've notified our team. Someone will reply shortly."


async def handle_incoming(db: Session, msg: IncomingMessage) -> str | None:
    settings = get_settings()
    profile = knowledge.load_business(msg.business_id)

    customer = personalization.get_or_create_customer(
        db,
        business_id=msg.business_id,
        platform=msg.platform.value,
        platform_user_id=msg.platform_user_id,
        display_name=msg.display_name,
    )

    if msg.text:
        detected = personalization.detect_language(msg.text, customer.language)
        if detected != customer.language:
            customer.language = detected
            db.commit()

    _log_message(db, msg, "in", msg.text or f"[{msg.message_type.value}]")

    # HUMAN handoff keyword
    if msg.text and msg.text.strip().upper() == settings.human_handoff_keyword:
        reply = await _handle_human_handoff(db, msg, profile, customer)
        await messaging.send_message(
            OutgoingMessage(
                platform=msg.platform,
                platform_user_id=msg.platform_user_id,
                text=reply,
                business_id=msg.business_id,
            )
        )
        _log_message(db, msg, "out", reply)
        return reply

    state = _get_state(db, msg)
    if state.state == "human":
        owner_chat = profile.owner_telegram_chat_id
        if owner_chat:
            await messaging.notify_owner_telegram(
                owner_chat,
                f"💬 Customer ({msg.platform.value}/{msg.platform_user_id}): "
                f"{msg.text or '[photo]'}",
            )
        reply = (
            "Our team is handling your chat. Please wait for a reply."
            if customer.language == "en"
            else "Yɛn staff re wo ho. Twɛ kakra."
        )
        await messaging.send_message(
            OutgoingMessage(
                platform=msg.platform,
                platform_user_id=msg.platform_user_id,
                text=reply,
                business_id=msg.business_id,
            )
        )
        return reply

    # After hours
    if not hours.is_open_now(profile):
        reply = hours.after_hours_message(profile, customer.language)
        await messaging.send_message(
            OutgoingMessage(
                platform=msg.platform,
                platform_user_id=msg.platform_user_id,
                text=reply,
                business_id=msg.business_id,
            )
        )
        _log_message(db, msg, "out", reply)
        return reply

    reply: str

    # Image handling
    if msg.message_type == MessageType.IMAGE:
        image_bytes = msg.media_bytes
        mime = msg.media_mime_type or "image/jpeg"
        if not image_bytes and msg.media_url:
            if msg.platform == Platform.WHATSAPP:
                image_bytes, mime = await wa_service.download_media(msg.media_url)
            elif msg.platform == Platform.TELEGRAM:
                from app.services.telegram_client import get_file_path
                from app.services.media import download_telegram_file

                path = await get_file_path(msg.media_url)
                image_bytes = await download_telegram_file(settings.telegram_bot_token, path)

        if image_bytes:
            reply = await vision.analyze_product_photo(
                profile,
                image_bytes,
                mime_type=mime,
                user_caption=msg.text or "",
                language=customer.language,
            )
        else:
            reply = "I couldn't download that image. Please try again or reply HUMAN."
    elif msg.text:
        ctx = personalization.customer_context(customer)
        reply = await ai.generate_reply(
            profile,
            msg.text,
            language=customer.language,
            customer_context=ctx,
        )

        # Lead detection
        catalog_names = [item.get("name", "") for item in profile.catalog]
        interest = leads.detect_interest(msg.text, catalog_names)
        phone = leads.extract_phone(msg.text)
        if interest or phone:
            lead = leads.create_lead(
                db,
                business_id=msg.business_id,
                platform=msg.platform.value,
                platform_user_id=msg.platform_user_id,
                customer_name=customer.display_name,
                phone=phone,
                interest=interest,
                notes=msg.text[:500],
            )
            if profile.owner_telegram_chat_id:
                await messaging.notify_owner_telegram(
                    profile.owner_telegram_chat_id,
                    leads.format_lead_notification(lead),
                )
    else:
        reply = "Send me a message or photo, or reply HUMAN to reach our team."

    await messaging.send_message(
        OutgoingMessage(
            platform=msg.platform,
            platform_user_id=msg.platform_user_id,
            text=reply,
            business_id=msg.business_id,
        )
    )
    _log_message(db, msg, "out", reply)
    return reply
