from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderOut

router = APIRouter(prefix="/orders")

@router.get("/{order_id}", response_model=OrderOut)
def get_(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    return o

@router.get("", response_model=list[OrderOut])
def list_(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == OrderStatus(status))
    return q.order_by(Order.id.desc()).all()
