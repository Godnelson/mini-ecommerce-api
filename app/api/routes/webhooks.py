from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.stripe_service import verify_webhook
from app.services.webhook_service import process_stripe_event

router = APIRouter(prefix="/webhooks")

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    event = verify_webhook(payload, stripe_signature or "")
    return process_stripe_event(db, event)
