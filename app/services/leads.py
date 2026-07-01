"""Lead capture and management."""

from __future__ import annotations

import logging
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Lead

logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"(?:\+233|0)[0-9]{9,10}")


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_RE.search(text.replace(" ", ""))
    return match.group(0) if match else None


def detect_interest(text: str, catalog_names: list[str]) -> Optional[str]:
    lower = text.lower()
    for name in catalog_names:
        if name.lower() in lower:
            return name
    buy_words = ["buy", "price", "cost", "order", "pɛ", "tua", "how much"]
    if any(w in lower for w in buy_words):
        return text[:200]
    return None


def create_lead(
    db: Session,
    *,
    business_id: str,
    platform: str,
    platform_user_id: str,
    customer_name: str | None = None,
    phone: str | None = None,
    interest: str | None = None,
    notes: str | None = None,
) -> Lead:
    lead = Lead(
        business_id=business_id,
        platform=platform,
        platform_user_id=platform_user_id,
        customer_name=customer_name,
        phone=phone,
        interest=interest,
        notes=notes,
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    logger.info("Lead #%s created for %s/%s", lead.id, platform, platform_user_id)
    return lead


def format_lead_notification(lead: Lead) -> str:
    return (
        f"🆕 New lead #{lead.id}\n"
        f"Platform: {lead.platform}\n"
        f"User: {lead.platform_user_id}\n"
        f"Name: {lead.customer_name or '—'}\n"
        f"Phone: {lead.phone or '—'}\n"
        f"Interest: {lead.interest or '—'}\n"
        f"Notes: {lead.notes or '—'}"
    )


def get_new_leads_since(db: Session, business_id: str, since) -> list[Lead]:
    return (
        db.query(Lead)
        .filter(Lead.business_id == business_id, Lead.created_at >= since, Lead.status == "new")
        .order_by(Lead.created_at.desc())
        .all()
    )
