from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.order import CheckoutOut, OrderOut
from app.services.checkout_service import checkout

router = APIRouter(prefix="/checkout")

@router.post("/{cart_id}", response_model=CheckoutOut)
def start(cart_id: int, db: Session = Depends(get_db)):
    order, session = checkout(db, cart_id)
    return {"order_id": order.id, "session_id": session["id"], "checkout_url": session["url"]}
