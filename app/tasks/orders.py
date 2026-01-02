from __future__ import annotations
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.db import init_db, SessionLocal
from app.models.order import Order, OrderStatus

@celery_app.task(name="post_payment_pipeline")
def post_payment_pipeline(order_id: int):
    """Post-payment pipeline.

    In this project, stock is **reserved at checkout** under a DB row lock.
    After payment confirmation we simply mark the order as fulfilled.
    """
    init_db(settings.DATABASE_URL)
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.paid:
            return

        order.status = OrderStatus.fulfilled
        db.commit()
    finally:
        db.close()
