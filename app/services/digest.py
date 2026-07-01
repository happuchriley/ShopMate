"""Morning digest scheduler — 8 AM Africa/Accra."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Lead, SessionLocal
from app.services import knowledge, messaging

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def send_morning_digest_for_business(business_id: str) -> None:
    settings = get_settings()
    profile = knowledge.load_business(business_id)
    owner_chat = profile.owner_telegram_chat_id
    if not owner_chat:
        logger.info("No owner chat for %s — skipping digest", business_id)
        return

    tz = ZoneInfo(profile.timezone or settings.default_timezone)
    now = datetime.now(tz)
    since = now - timedelta(hours=24)

    db: Session = SessionLocal()
    try:
        new_leads = (
            db.query(Lead)
            .filter(Lead.business_id == business_id, Lead.created_at >= since.replace(tzinfo=None))
            .order_by(Lead.created_at.desc())
            .all()
        )
    finally:
        db.close()

    lines = [
        f"☀️ Good morning! ShopMate digest for {profile.name}",
        f"📅 {now.strftime('%A, %d %B %Y')}",
        "",
        f"New leads (24h): {len(new_leads)}",
    ]
    for lead in new_leads[:10]:
        lines.append(f"  • #{lead.id} — {lead.interest or 'General'} ({lead.platform})")
    if not new_leads:
        lines.append("  No new leads yesterday.")
    lines.append("")
    lines.append("Have a great day! 🚀")

    await messaging.notify_owner_telegram(owner_chat, "\n".join(lines))
    logger.info("Morning digest sent for %s", business_id)


async def _run_all_digests() -> None:
    settings = get_settings()
    for biz_id in knowledge.list_businesses():
        try:
            await send_morning_digest_for_business(biz_id)
        except Exception as exc:
            logger.exception("Digest failed for %s: %s", biz_id, exc)


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    settings = get_settings()
    if _scheduler is not None:
        return _scheduler

    tz = ZoneInfo(settings.default_timezone)
    _scheduler = AsyncIOScheduler(timezone=tz)
    _scheduler.add_job(
        _run_all_digests,
        trigger="cron",
        hour=settings.digest_hour,
        minute=settings.digest_minute,
        id="morning_digest",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Digest scheduler started — %02d:%02d %s",
        settings.digest_hour,
        settings.digest_minute,
        settings.default_timezone,
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
