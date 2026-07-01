"""Business knowledge loading from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.config import get_settings


@dataclass
class BusinessProfile:
    business_id: str
    name: str
    tagline: str = ""
    timezone: str = "Africa/Accra"
    language_default: str = "en"
    languages: list[str] = field(default_factory=lambda: ["en", "twi"])
    owner_telegram_chat_id: str | None = None
    owner_whatsapp_number: str | None = None
    hours: dict[str, Any] = field(default_factory=dict)
    catalog: list[dict[str, Any]] = field(default_factory=list)
    faq: list[dict[str, str]] = field(default_factory=list)
    services: list[dict[str, Any]] = field(default_factory=list)
    policies: dict[str, str] = field(default_factory=dict)
    raw_config: dict[str, Any] = field(default_factory=dict)
    raw_knowledge: dict[str, Any] = field(default_factory=dict)

    def knowledge_context(self) -> str:
        lines = [
            f"Business: {self.name}",
            f"Tagline: {self.tagline}",
            "",
            "Catalog:",
        ]
        for item in self.catalog:
            name = item.get("name", "")
            price = item.get("price_ghs", item.get("price", ""))
            desc = item.get("description", "")
            stock = item.get("in_stock", True)
            lines.append(f"- {name}: GHS {price} — {desc} (in stock: {stock})")

        if self.services:
            lines.append("")
            lines.append("Services / Repairs:")
            for svc in self.services:
                lines.append(
                    f"- {svc.get('name', '')}: {svc.get('description', '')} "
                    f"(from GHS {svc.get('price_from_ghs', svc.get('price', 'N/A'))})"
                )

        if self.faq:
            lines.append("")
            lines.append("FAQ:")
            for entry in self.faq:
                lines.append(f"Q: {entry.get('q', entry.get('question', ''))}")
                lines.append(f"A: {entry.get('a', entry.get('answer', ''))}")

        if self.policies:
            lines.append("")
            lines.append("Policies:")
            for key, value in self.policies.items():
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def load_business(business_id: str, businesses_dir: Path | None = None) -> BusinessProfile:
    settings = get_settings()
    base = businesses_dir or settings.businesses_dir
    biz_dir = base / business_id
    config = _load_yaml(biz_dir / "config.yaml")
    knowledge = _load_yaml(biz_dir / "knowledge.yaml")

    return BusinessProfile(
        business_id=business_id,
        name=config.get("name", knowledge.get("name", business_id)),
        tagline=config.get("tagline", knowledge.get("tagline", "")),
        timezone=config.get("timezone", settings.default_timezone),
        language_default=config.get("language_default", settings.default_language),
        languages=config.get("languages", ["en", "twi"]),
        owner_telegram_chat_id=str(config.get("owner_telegram_chat_id") or "") or None,
        owner_whatsapp_number=config.get("owner_whatsapp_number"),
        hours=config.get("hours", knowledge.get("hours", {})),
        catalog=knowledge.get("catalog", knowledge.get("products", [])),
        faq=knowledge.get("faq", []),
        services=knowledge.get("services", knowledge.get("repairs", [])),
        policies=knowledge.get("policies", config.get("policies", {})),
        raw_config=config,
        raw_knowledge=knowledge,
    )


def list_businesses(businesses_dir: Path | None = None) -> list[str]:
    settings = get_settings()
    base = businesses_dir or settings.businesses_dir
    if not base.exists():
        return []
    return sorted(
        p.name for p in base.iterdir() if p.is_dir() and (p / "config.yaml").exists()
    )
