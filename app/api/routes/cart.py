from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.cart import CartCreateOut, CartItemAdd, CartItemPatch, CartOut
from app.services.cart_service import create_cart, get_cart, add_item, patch_item_qty, delete_item, cart_totals, expire_cart

router = APIRouter(prefix="/cart")

@router.post("", response_model=CartCreateOut, status_code=201)
def create(db: Session = Depends(get_db)):
    c = create_cart(db)
    return {"id": c.id, "status": c.status.value}

@router.get("/{cart_id}", response_model=CartOut)
def get_(cart_id: int, db: Session = Depends(get_db)):
    c = get_cart(db, cart_id)
    total, currency = cart_totals(c)
    return {"id": c.id, "status": c.status.value, "items": c.items, "total_cents": total, "currency": currency}

@router.post("/{cart_id}/items", response_model=CartOut)
def add(cart_id: int, payload: CartItemAdd, db: Session = Depends(get_db)):
    c = add_item(db, cart_id, payload.product_id, payload.qty)
    total, currency = cart_totals(c)
    return {"id": c.id, "status": c.status.value, "items": c.items, "total_cents": total, "currency": currency}

@router.patch("/{cart_id}/items/{item_id}", response_model=CartOut)
def patch_item(cart_id: int, item_id: int, payload: CartItemPatch, db: Session = Depends(get_db)):
    c = patch_item_qty(db, cart_id, item_id, payload.qty)
    total, currency = cart_totals(c)
    return {"id": c.id, "status": c.status.value, "items": c.items, "total_cents": total, "currency": currency}

@router.delete("/{cart_id}/items/{item_id}", response_model=CartOut)
def delete_item_(cart_id: int, item_id: int, db: Session = Depends(get_db)):
    c = delete_item(db, cart_id, item_id)
    total, currency = cart_totals(c)
    return {"id": c.id, "status": c.status.value, "items": c.items, "total_cents": total, "currency": currency}

@router.post("/{cart_id}/expire")
def expire(cart_id: int, db: Session = Depends(get_db)):
    expire_cart(db, cart_id)
    return {"status": "ok"}
