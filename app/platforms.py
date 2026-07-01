"""Platform and message type definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Platform(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


@dataclass
class IncomingMessage:
    """Normalized inbound message from any platform."""

    platform: Platform
    platform_user_id: str
    business_id: str
    message_type: MessageType
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_bytes: Optional[bytes] = None
    media_mime_type: Optional[str] = None
    display_name: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)
    message_id: Optional[str] = None


@dataclass
class OutgoingMessage:
    """Normalized outbound message to any platform."""

    platform: Platform
    platform_user_id: str
    text: str
    business_id: str = ""
    parse_mode: Optional[str] = None
