from __future__ import annotations
from sqlalchemy import String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_id", name="uq_provider_event_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(30), default="stripe", index=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    processed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
