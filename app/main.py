"""ShopMate FastAPI application — WhatsApp webhook + Telegram polling."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app import __version__
from app.config import get_settings, validate_config
from app.db.models import get_db, init_db
from app.services import digest, handler, telegram_bot, whatsapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    errors = validate_config(settings)
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        logger.warning("Starting with configuration warnings — some features may be unavailable")

    init_db()
    digest.start_scheduler()
    await telegram_bot.start_polling()
    logger.info("ShopMate v%s started", __version__)
    yield
    await telegram_bot.stop_polling()
    digest.stop_scheduler()
    logger.info("ShopMate shut down")


app = FastAPI(
    title="ShopMate",
    description="WhatsApp + Telegram business assistant",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "name": "ShopMate",
        "version": __version__,
        "status": "running",
        "channels": ["whatsapp", "telegram"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/webhook")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("WhatsApp webhook verified")
        return PlainTextResponse(content=hub_challenge or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not whatsapp.verify_signature(body_bytes, signature):
        logger.warning("Invalid WhatsApp webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    body = json.loads(body_bytes)
    settings = get_settings()
    messages = whatsapp.parse_webhook(body, settings.default_business_id)

    for msg in messages:
        try:
            await handler.handle_incoming(db, msg)
        except Exception as exc:
            logger.exception("Error handling WhatsApp message: %s", exc)

    return Response(status_code=200)


if __name__ == "__main__":
    import uvicorn

    cfg = get_settings()
    uvicorn.run("app.main:app", host=cfg.host, port=cfg.port, reload=cfg.debug)
