from __future__ import annotations
import enum
from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

class OrderStatus(str, enum.Enum):
    pending_payment = "PENDING_PAYMENT"
    paid = "PAID"
    fulfilled = "FULFILLED"
    cancelled = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), unique=True, index=True)
    total_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="brl")
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), default=OrderStatus.pending_payment, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all,delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all,delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    qty: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(Integer)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
