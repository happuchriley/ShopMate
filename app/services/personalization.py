"""Customer personalization and preferences."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Customer


def get_or_create_customer(
    db: Session,
    *,
    business_id: str,
    platform: str,
    platform_user_id: str,
    display_name: str | None = None,
    language: str = "en",
) -> Customer:
    customer = (
        db.query(Customer)
        .filter_by(
            business_id=business_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )
        .first()
    )
    if customer:
        customer.last_seen_at = datetime.utcnow()
        if display_name:
            customer.display_name = display_name
        db.commit()
        db.refresh(customer)
        return customer

    customer = Customer(
        business_id=business_id,
        platform=platform,
        platform_user_id=platform_user_id,
        display_name=display_name,
        language=language,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_preferences(customer: Customer) -> dict[str, Any]:
    try:
        return json.loads(customer.preferences_json or "{}")
    except json.JSONDecodeError:
        return {}


def set_preference(customer: Customer, db: Session, key: str, value: Any) -> None:
    prefs = get_preferences(customer)
    prefs[key] = value
    customer.preferences_json = json.dumps(prefs)
    db.commit()


def detect_language(text: str, current: str = "en") -> str:
    """Simple Twi hint detection; defaults to current language."""
    twi_markers = [
        "me pɛ", "ɛte sɛn", "medaase", "meda wo ase", "wo ho", "sɛn",
        "me paa", "yɛ", "wɔ", "bi", "kakra", "ma me", "hwɛ",
    ]
    lower = text.lower()
    if any(m in lower for m in twi_markers):
        return "twi"
    return current


def customer_context(customer: Customer) -> str:
    prefs = get_preferences(customer)
    parts = [
        f"Name: {customer.display_name or 'Unknown'}",
        f"Language: {customer.language}",
        f"Platform: {customer.platform}",
    ]
    if prefs:
        parts.append(f"Preferences: {json.dumps(prefs)}")
    return "\n".join(parts)
