from __future__ import annotations
import enum
from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

class PaymentStatus(str, enum.Enum):
    initiated = "INITIATED"
    succeeded = "SUCCEEDED"
    failed = "FAILED"
    refunded = "REFUNDED"

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="stripe")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.initiated, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="brl")
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), index=True, default=None)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), index=True, default=None)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payment")
