from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartStatus
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.services.stripe_service import create_checkout_session
from app.tasks.carts import expire_cart_later
from app.tasks.orders import post_payment_pipeline


def checkout(db: Session, cart_id: int) -> tuple[Order, dict]:
    """Create an order/payment and return a Stripe Checkout session.

    Concurrency correctness:
    - Reserves stock at checkout (row lock + decrement) to prevent overselling.
    - A background task may later expire the cart and restore stock if payment never happens.
    """
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if cart.status != CartStatus.active:
        raise HTTPException(status_code=400, detail="Cart not active")
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Reserve stock atomically
    product_ids = [i.product_id for i in cart.items]
    products = (
        db.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .with_for_update()
        )
        .scalars()
        .all()
    )
    by_id = {p.id: p for p in products}

    total = 0
    currency = cart.items[0].product.currency
    for item in cart.items:
        p = by_id.get(item.product_id)
        if not p or not p.active:
            raise HTTPException(status_code=409, detail="Product inactive")
        if p.stock < item.qty:
            raise HTTPException(status_code=409, detail="Insufficient stock")
        p.stock -= item.qty  # reserve
        total += item.qty * item.unit_price_cents

    # Create order + items (still within the same transaction)
    order = Order(cart_id=cart.id, total_cents=total, currency=currency, status=OrderStatus.pending_payment.value)
    db.add(order)
    db.flush()

    for item in cart.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                qty=item.qty,
                unit_price_cents=item.unit_price_cents,
            )
        )

    payment = Payment(order_id=order.id, amount_cents=total, currency=currency, status=PaymentStatus.initiated)
    db.add(payment)

    cart.status = CartStatus.checked_out
    db.commit()
    db.refresh(order)

    # Create Stripe session (external call) after commit
    session = create_checkout_session(order_id=order.id, amount_cents=total, currency=currency)

    # Save session id
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    payment.stripe_session_id = session["id"]
    db.commit()

    # schedule cart expiry safety net (30min)
    try:
        expire_cart_later.apply_async(args=[cart.id], countdown=1800)
    except Exception:
        pass

    return order, session


def mark_order_paid(
    db: Session,
    *,
    stripe_session_id: str | None,
    payment_intent_id: str | None,
    order_id: int | None,
):
    """Mark payment as succeeded and move the order to PAID (idempotent)."""
    q = db.query(Payment)
    if order_id is not None:
        q = q.filter(Payment.order_id == order_id)
    elif stripe_session_id:
        q = q.filter(Payment.stripe_session_id == stripe_session_id)
    else:
        raise HTTPException(status_code=400, detail="Cannot locate payment")

    payment = q.first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.succeeded:
        return payment.order  # idempotent

    payment.status = PaymentStatus.succeeded
    if payment_intent_id:
        payment.stripe_payment_intent_id = payment_intent_id

    order = payment.order
    order.status = OrderStatus.paid
    db.commit()
    db.refresh(order)

    # async pipeline (fulfillment)
    try:
        post_payment_pipeline.delay(order.id)
    except Exception:
        pass

    return order
