import json

async def test_checkout_and_webhook_happy_path(client, monkeypatch):
    # create category
    cat = (await client.post("/categories", json={"name": "Games"})).json()

    # create product
    prod = (await client.post("/products", json={
        "category_id": cat["id"],
        "name": "Nier Poster",
        "description": "fake",
        "price_cents": 1000,
        "currency": "brl",
        "stock": 10,
        "active": True,
    })).json()

    cart = (await client.post("/cart")).json()
    await client.post(f"/cart/{cart['id']}/items", json={"product_id": prod["id"], "qty": 2})

    # mock stripe session create
    def fake_create_session(*args, **kwargs):
        return {"id": "cs_test_123", "url": "https://fake.checkout/123"}

    monkeypatch.setattr("app.services.checkout_service.create_checkout_session", fake_create_session)

    checkout = (await client.post(f"/checkout/{cart['id']}")).json()
    assert checkout["session_id"] == "cs_test_123"
    order_id = checkout["order_id"]

    # webhook verify mock
    fake_event = {
        "id": "evt_1",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_123", "payment_intent": "pi_1", "metadata": {"order_id": str(order_id)}}},
    }

    def fake_verify(payload, sig):
        return fake_event

    monkeypatch.setattr("app.api.routes.webhooks.verify_webhook", fake_verify)

    resp = await client.post("/webhooks/stripe", content=json.dumps(fake_event), headers={"Stripe-Signature": "t=fake"})
    assert resp.status_code == 200

    order = (await client.get(f"/orders/{order_id}")).json()
    assert order["status"] == "PAID"

async def test_webhook_idempotent(client, monkeypatch):
    cat = (await client.post("/categories", json={"name": "Books"})).json()
    prod = (await client.post("/products", json={
        "category_id": cat["id"], "name": "Book", "price_cents": 500, "currency": "brl", "stock": 10, "active": True
    })).json()
    cart = (await client.post("/cart")).json()
    await client.post(f"/cart/{cart['id']}/items", json={"product_id": prod["id"], "qty": 1})

    def fake_create_session(*args, **kwargs):
        return {"id": "cs_test_999", "url": "https://fake.checkout/999"}
    monkeypatch.setattr("app.services.checkout_service.create_checkout_session", fake_create_session)

    checkout = (await client.post(f"/checkout/{cart['id']}")).json()
    order_id = checkout["order_id"]

    fake_event = {
        "id": "evt_same",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_999", "payment_intent": "pi_999", "metadata": {"order_id": str(order_id)}}},
    }
    def fake_verify(payload, sig):
        return fake_event
    monkeypatch.setattr("app.api.routes.webhooks.verify_webhook", fake_verify)

    r1 = await client.post("/webhooks/stripe", content=json.dumps(fake_event), headers={"Stripe-Signature": "t=fake"})
    r2 = await client.post("/webhooks/stripe", content=json.dumps(fake_event), headers={"Stripe-Signature": "t=fake"})
    assert r1.status_code == 200
    assert r2.status_code == 200

    order = (await client.get(f"/orders/{order_id}")).json()
    assert order["status"] == "PAID"
