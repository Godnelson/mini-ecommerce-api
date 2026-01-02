from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from app.models.cart import Cart, CartItem, CartStatus
from app.models.product import Product
from app.models.order import Order, OrderStatus

def create_cart(db: Session) -> Cart:
    c = Cart(status=CartStatus.active)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def get_cart(db: Session, cart_id: int) -> Cart:
    c = db.query(Cart).filter(Cart.id == cart_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cart not found")
    return c

def cart_totals(cart: Cart):
    total = sum(i.qty * i.unit_price_cents for i in cart.items)
    currency = cart.items[0].product.currency if cart.items else "brl"
    return total, currency

def add_item(db: Session, cart_id: int, product_id: int, qty: int) -> Cart:
    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be > 0")
    cart = get_cart(db, cart_id)
    if cart.status != CartStatus.active:
        raise HTTPException(status_code=400, detail="cart not active")

    product = db.query(Product).filter(Product.id == product_id, Product.active.is_(True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < qty:
        raise HTTPException(status_code=409, detail="Insufficient stock")

    existing = db.query(CartItem).filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id).first()
    if existing:
        new_qty = existing.qty + qty
        if product.stock < new_qty:
            raise HTTPException(status_code=409, detail="Insufficient stock")
        existing.qty = new_qty
    else:
        item = CartItem(cart_id=cart_id, product_id=product_id, qty=qty, unit_price_cents=product.price_cents)
        db.add(item)

    db.commit()
    db.refresh(cart)
    return cart

def patch_item_qty(db: Session, cart_id: int, item_id: int, qty: int) -> Cart:
    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be > 0")
    cart = get_cart(db, cart_id)
    if cart.status != CartStatus.active:
        raise HTTPException(status_code=400, detail="cart not active")

    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    product = item.product
    if product.stock < qty:
        raise HTTPException(status_code=409, detail="Insufficient stock")

    item.qty = qty
    db.commit()
    db.refresh(cart)
    return cart

def delete_item(db: Session, cart_id: int, item_id: int) -> Cart:
    cart = get_cart(db, cart_id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
def expire_cart(db: Session, cart_id: int):
    """Expire a cart and (if needed) release reserved stock.

    Stock is reserved at checkout (rows locked + stock decremented). If the payment
    never completes, we cancel the pending order and restore stock.
    """
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        return

    # If still active, just expire
    if cart.status == CartStatus.active:
        cart.status = CartStatus.expired
        db.commit()
        return

    # If checked out, try to cancel the pending order and release stock
    if cart.status == CartStatus.checked_out:
        order = db.query(Order).filter(Order.cart_id == cart.id).first()
        if not order:
            cart.status = CartStatus.expired
            db.commit()
            return

        # Only cancel if payment is still pending
        if order.status != OrderStatus.pending_payment:
            return

        # Lock product rows and restore stock
        product_ids = [it.product_id for it in order.items]
        products = db.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .with_for_update()
        ).scalars().all()
        by_id = {p.id: p for p in products}

        for it in order.items:
            p = by_id.get(it.product_id)
            if p:
                p.stock += it.qty

        order.status = OrderStatus.cancelled
        cart.status = CartStatus.expired
        db.commit()
    if cart.status == CartStatus.active:
        cart.status = CartStatus.expired
        db.commit()
