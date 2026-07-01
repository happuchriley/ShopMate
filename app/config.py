"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
BUSINESSES_DIR = ROOT_DIR / "businesses"


def normalize_database_url(url: str) -> str:
    """Railway/Render/Heroku use postgres:// — SQLAlchemy 2 needs postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'shopmate.db'}")
)
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Africa/Accra")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "8"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))


@dataclass
class Config:
    """Runtime configuration."""

    telegram_bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_api_version: str = "v21.0"
    database_url: str = DATABASE_URL
    businesses_dir: Path = field(default_factory=lambda: BUSINESSES_DIR)
    default_business_id: str = "techlink_mobile"
    default_timezone: str = DEFAULT_TIMEZONE
    default_language: str = DEFAULT_LANGUAGE
    digest_hour: int = DIGEST_HOUR
    digest_minute: int = DIGEST_MINUTE
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    human_handoff_keyword: str = "HUMAN"
    after_hours_message_en: str = (
        "Thanks for reaching out! We're currently closed. "
        "We'll reply when we open. Reply HUMAN to speak with staff."
    )
    after_hours_message_twi: str = (
        "Meda wo ase! Yɛn adwuma bere no awie. "
        "Yɛbɛbɔ wo ho amanneɛ bere a yɛbɛbue. Fa HUMAN kyerɛ sɛ wopɛ sɛ wokasa ne yɛn."
    )

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            whatsapp_verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip(),
            whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip(),
            whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
            whatsapp_app_secret=os.getenv("WHATSAPP_APP_SECRET", "").strip(),
            whatsapp_api_version=os.getenv("WHATSAPP_API_VERSION", "v21.0").strip(),
            database_url=os.getenv("DATABASE_URL", DATABASE_URL),
            default_business_id=os.getenv("DEFAULT_BUSINESS_ID", "techlink_mobile").strip(),
            default_timezone=os.getenv("DEFAULT_TIMEZONE", DEFAULT_TIMEZONE).strip(),
            default_language=os.getenv("DEFAULT_LANGUAGE", DEFAULT_LANGUAGE).strip(),
            digest_hour=int(os.getenv("DIGEST_HOUR", str(DIGEST_HOUR))),
            digest_minute=int(os.getenv("DIGEST_MINUTE", str(DIGEST_MINUTE))),
            host=os.getenv("HOST", "0.0.0.0").strip(),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() in ("1", "true", "yes"),
            human_handoff_keyword=os.getenv("HUMAN_HANDOFF_KEYWORD", "HUMAN").strip().upper(),
        )


def whatsapp_enabled(cfg: Config) -> bool:
    return bool(cfg.whatsapp_access_token and cfg.whatsapp_phone_number_id)


def validate_config(cfg: Config) -> list[str]:
    """Return list of configuration errors (empty if valid)."""
    errors: list[str] = []
    placeholder_keys = {
        "",
        "YOUR_OPENAI_API_KEY_HERE",
        "changeme",
        "placeholder",
        "your_openai_api_key",
    }

    if not cfg.telegram_bot_token:
        errors.append("TELEGRAM_BOT_TOKEN is required for Telegram polling.")

    if not cfg.openai_api_key or cfg.openai_api_key in placeholder_keys:
        errors.append("OPENAI_API_KEY is required and must not be a placeholder.")

    whatsapp_partial = bool(
        cfg.whatsapp_access_token
        or cfg.whatsapp_phone_number_id
        or cfg.whatsapp_app_secret
    )
    if whatsapp_partial and not cfg.whatsapp_verify_token:
        errors.append(
            "WHATSAPP_VERIFY_TOKEN is required when any WhatsApp env var is set."
        )

    if cfg.whatsapp_access_token and not cfg.whatsapp_phone_number_id:
        errors.append("WHATSAPP_PHONE_NUMBER_ID is required when WHATSAPP_ACCESS_TOKEN is set.")

    if cfg.whatsapp_phone_number_id and not cfg.whatsapp_access_token:
        errors.append("WHATSAPP_ACCESS_TOKEN is required when WHATSAPP_PHONE_NUMBER_ID is set.")

    if not cfg.businesses_dir.exists():
        errors.append(f"Businesses directory not found: {cfg.businesses_dir}")

    default_biz = cfg.businesses_dir / cfg.default_business_id
    if not default_biz.exists():
        errors.append(f"Default business not found: {default_biz}")

    return errors


_settings: Optional[Config] = None


def get_settings() -> Config:
    global _settings
    if _settings is None:
        _settings = Config.from_env()
    return _settings
