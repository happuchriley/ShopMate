#!/usr/bin/env python3
"""Onboard a new business into ShopMate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
BUSINESSES = ROOT / "businesses"

TEMPLATE_MAP = {
    "retail": "retail.yaml",
    "salon": "salon.yaml",
    "restaurant": "restaurant.yaml",
    "services": "services.yaml",
}


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Onboard a new ShopMate business")
    parser.add_argument("name", help="Business display name")
    parser.add_argument("--template", choices=TEMPLATE_MAP.keys(), default="retail")
    parser.add_argument("--tagline", default="Your friendly local business")
    parser.add_argument("--id", dest="business_id", help="Business folder ID (auto-generated if omitted)")
    args = parser.parse_args()

    business_id = args.business_id or slugify(args.name)
    biz_dir = BUSINESSES / business_id
    if biz_dir.exists():
        print(f"Error: business already exists at {biz_dir}")
        return 1

    template_file = TEMPLATES / TEMPLATE_MAP[args.template]
    if not template_file.exists():
        print(f"Error: template not found: {template_file}")
        return 1

    biz_dir.mkdir(parents=True)
    config_text = template_file.read_text(encoding="utf-8")
    config_text = config_text.replace("{{BUSINESS_NAME}}", args.name)
    config_text = config_text.replace("{{TAGLINE}}", args.tagline)
    (biz_dir / "config.yaml").write_text(config_text, encoding="utf-8")

    knowledge = {
        "name": args.name,
        "tagline": args.tagline,
        "catalog": [],
        "services": [],
        "faq": [
            {"q": "Where are you located?", "a": "Update this in knowledge.yaml"},
            {"q": "What are your hours?", "a": "See config.yaml hours section"},
        ],
        "policies": {},
    }
    with (biz_dir / "knowledge.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(knowledge, f, default_flow_style=False, allow_unicode=True)

    print(f"✅ Created business: {business_id}")
    print(f"   Config:  {biz_dir / 'config.yaml'}")
    print(f"   Knowledge: {biz_dir / 'knowledge.yaml'}")
    print("   Edit knowledge.yaml with your catalog, FAQ, and services.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
