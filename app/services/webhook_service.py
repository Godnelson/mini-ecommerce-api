from __future__ import annotations
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.webhook_event import WebhookEvent
from app.services.checkout_service import mark_order_paid

def process_stripe_event(db: Session, event: dict):
    event_id = event.get("id")
    event_type = event.get("type")
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Invalid event")

    # idempotency
    existing = db.query(WebhookEvent).filter(WebhookEvent.provider == "stripe", WebhookEvent.event_id == event_id).first()
    if existing:
        return {"status": "ok", "idempotent": True}

    db.add(WebhookEvent(provider="stripe", event_id=event_id))
    db.commit()

    obj = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        session_id = obj.get("id")
        metadata = obj.get("metadata") or {}
        order_id = metadata.get("order_id")
        order_id_int = int(order_id) if order_id else None
        order = mark_order_paid(db, stripe_session_id=session_id, payment_intent_id=obj.get("payment_intent"), order_id=order_id_int)
        return {"status": "ok", "order_id": order.id}

    # you can add more event types here:
    # payment_intent.succeeded, charge.refunded, etc.
    return {"status": "ok"}
