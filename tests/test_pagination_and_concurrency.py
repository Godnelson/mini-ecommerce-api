import threading
import pytest
from sqlalchemy.orm import sessionmaker

from app.models.category import Category
from app.models.product import Product
from app.models.cart import Cart, CartItem, CartStatus
from app.services.checkout_service import checkout
import app.services.stripe_service as stripe_service


@pytest.mark.asyncio
async def test_products_cursor_pagination(client):
    # create category
    resp = await client.post("/categories", json={"name": "Teclados"})
    assert resp.status_code == 201
    cat = resp.json()

    # create 5 products
    for i in range(5):
        r = await client.post(
            "/products",
            json={
                "category_id": cat["id"],
                "name": f"Produto {i}",
                "description": None,
                "price_cents": 1000 + i,
                "currency": "brl",
                "stock": 10,
                "active": True,
            },
        )
        assert r.status_code == 201

    r1 = await client.get("/products", params={"limit": 2})
    assert r1.status_code == 200
    page1 = r1.json()
    assert len(page1["items"]) == 2
    assert page1["next_cursor"] is not None

    r2 = await client.get("/products", params={"limit": 2, "after_id": page1["next_cursor"]})
    assert r2.status_code == 200
    page2 = r2.json()
    assert len(page2["items"]) == 2

    # ensure no duplicates between pages
    ids1 = {p["id"] for p in page1["items"]}
    ids2 = {p["id"] for p in page2["items"]}
    assert ids1.isdisjoint(ids2)


def test_checkout_stock_reservation_is_concurrency_safe(engine, monkeypatch):
    # avoid real Stripe call
    monkeypatch.setattr(
        stripe_service,
        "create_checkout_session",
        lambda **kwargs: {"id": "cs_test", "url": "https://example.test/checkout"},
    )

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # setup data
    db = SessionLocal()
    try:
        cat = Category(name="Cat", slug="cat")
        db.add(cat)
        db.flush()

        p = Product(
            category_id=cat.id,
            name="P1",
            description=None,
            price_cents=1000,
            currency="brl",
            stock=1,
            active=True,
        )
        db.add(p)
        db.flush()

        c1 = Cart(status=CartStatus.active)
        c2 = Cart(status=CartStatus.active)
        db.add_all([c1, c2])
        db.flush()

        db.add_all(
            [
                CartItem(cart_id=c1.id, product_id=p.id, qty=1, unit_price_cents=1000),
                CartItem(cart_id=c2.id, product_id=p.id, qty=1, unit_price_cents=1000),
            ]
        )
        db.commit()
    finally:
        db.close()

    results = []
    errors = []
    barrier = threading.Barrier(2)

    def run_checkout(cart_id: int):
        s = SessionLocal()
        try:
            barrier.wait()
            order, _session = checkout(s, cart_id)
            results.append((cart_id, order.id))
        except Exception as e:
            errors.append((cart_id, str(e)))
            s.rollback()
        finally:
            s.close()

    # carts inserted above will have ids 1 and 2 in a fresh DB, but to be safe
    # we can query them back:
    db2 = SessionLocal()
    try:
        cart_ids = [c.id for c in db2.query(Cart).order_by(Cart.id.asc()).all()]
        assert len(cart_ids) >= 2
        c1_id, c2_id = cart_ids[0], cart_ids[1]
    finally:
        db2.close()

    t1 = threading.Thread(target=run_checkout, args=(c1_id,), daemon=True)
    t2 = threading.Thread(target=run_checkout, args=(c2_id,), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # exactly one should succeed, the other should fail with insufficient stock
    assert len(results) == 1
    assert len(errors) == 1
    assert "Insufficient stock" in errors[0][1]
