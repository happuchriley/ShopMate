"""SQLAlchemy models for ShopMate."""

from __future__ import annotations

from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    timezone = Column(String(64), default="Africa/Accra")
    owner_telegram_chat_id = Column(String(64), nullable=True)
    owner_whatsapp_number = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customers = relationship("Customer", back_populates="business")
    leads = relationship("Lead", back_populates="business")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(64), ForeignKey("businesses.id"), nullable=False)
    platform = Column(String(32), nullable=False)  # telegram | whatsapp
    platform_user_id = Column(String(128), nullable=False)
    display_name = Column(String(256), nullable=True)
    language = Column(String(8), default="en")
    preferences_json = Column(Text, default="{}")
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="customers")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(64), ForeignKey("businesses.id"), nullable=False)
    platform = Column(String(32), nullable=False)
    platform_user_id = Column(String(128), nullable=False)
    customer_name = Column(String(256), nullable=True)
    phone = Column(String(32), nullable=True)
    interest = Column(Text, nullable=True)
    status = Column(String(32), default="new")  # new | contacted | closed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="leads")


class ConversationState(Base):
    __tablename__ = "conversation_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(64), nullable=False)
    platform = Column(String(32), nullable=False)
    platform_user_id = Column(String(128), nullable=False)
    state = Column(String(64), default="bot")  # bot | human
    context_json = Column(Text, default="{}")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(64), nullable=False)
    platform = Column(String(32), nullable=False)
    platform_user_id = Column(String(128), nullable=False)
    direction = Column(String(8), nullable=False)  # in | out
    message_type = Column(String(32), default="text")
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


_settings = get_settings()
_connect_args = (
    {"check_same_thread": False}
    if _settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(_settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
