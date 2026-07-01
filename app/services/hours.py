"""Business hours and after-hours handling."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.services.knowledge import BusinessProfile


def _parse_time(value: str) -> tuple[int, int]:
    parts = value.strip().split(":")
    return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0


def is_open_now(profile: BusinessProfile, now: datetime | None = None) -> bool:
    tz = ZoneInfo(profile.timezone or get_settings().default_timezone)
    now = now or datetime.now(tz)
    hours: dict[str, Any] = profile.hours or {}
    day_key = now.strftime("%A").lower()
    day_hours = hours.get(day_key) or hours.get(day_key[:3])
    if not day_hours:
        return True
    if isinstance(day_hours, str) and day_hours.lower() in ("closed", "off"):
        return False
    if isinstance(day_hours, dict):
        if day_hours.get("closed"):
            return False
        open_str = day_hours.get("open", "08:00")
        close_str = day_hours.get("close", "18:00")
    elif isinstance(day_hours, list) and len(day_hours) >= 2:
        open_str, close_str = day_hours[0], day_hours[1]
    else:
        return True

    open_h, open_m = _parse_time(str(open_str))
    close_h, close_m = _parse_time(str(close_str))
    current = now.hour * 60 + now.minute
    start = open_h * 60 + open_m
    end = close_h * 60 + close_m
    return start <= current < end


def after_hours_message(profile: BusinessProfile, language: str = "en") -> str:
    settings = get_settings()
    hours = profile.hours or {}
    schedule_lines = []
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        val = hours.get(day, "08:00-18:00")
        if isinstance(val, dict):
            if val.get("closed"):
                val = "Closed"
            else:
                val = f"{val.get('open', '?')}-{val.get('close', '?')}"
        schedule_lines.append(f"{day.title()}: {val}")

    schedule = "\n".join(schedule_lines)
    if language == "twi":
        return (
            f"{settings.after_hours_message_twi}\n\n"
            f"📅 Bere:\n{schedule}"
        )
    return (
        f"{settings.after_hours_message_en}\n\n"
        f"📅 Hours:\n{schedule}"
    )


def format_hours(profile: BusinessProfile) -> str:
    hours = profile.hours or {}
    lines = [f"🕐 {profile.name} hours:"]
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        val = hours.get(day, "08:00-18:00")
        if isinstance(val, dict):
            if val.get("closed"):
                val = "Closed"
            else:
                val = f"{val.get('open', '?')} – {val.get('close', '?')}"
        lines.append(f"• {day.title()}: {val}")
    return "\n".join(lines)
