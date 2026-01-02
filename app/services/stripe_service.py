from __future__ import annotations
import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY

def create_checkout_session(*, order_id: int, amount_cents: int, currency: str) -> dict:
    # Note: in tests we monkeypatch this function, so no real Stripe calls are made.
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={"order_id": str(order_id)},
        line_items=[{
            "quantity": 1,
            "price_data": {
                "currency": currency,
                "unit_amount": amount_cents,
                "product_data": {"name": f"Order #{order_id}"},
            }
        }],
    )
    return {"id": session.id, "url": session.url}

def verify_webhook(payload: bytes, sig_header: str) -> dict:
    # In tests we monkeypatch this too.
    if settings.ALLOW_INSECURE_WEBHOOK and not settings.STRIPE_WEBHOOK_SECRET:
        # unsafe fallback
        return stripe.Event.construct_from(stripe.util.json.loads(payload.decode("utf-8")), stripe.api_key)

    event = stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig_header,
        secret=settings.STRIPE_WEBHOOK_SECRET,
    )
    # Convert to plain dict
    return stripe.util.convert_to_dict(event)
