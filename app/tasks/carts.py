from __future__ import annotations
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.db import init_db, SessionLocal
from app.services.cart_service import expire_cart

@celery_app.task(name="expire_cart_later")
def expire_cart_later(cart_id: int):
    # simple: expire after 30 minutes using countdown in celery beat in real life.
    # Here we just exist as a task hook for demo.
    init_db(settings.DATABASE_URL)
    db = SessionLocal()
    try:
        expire_cart(db, cart_id)
    finally:
        db.close()
