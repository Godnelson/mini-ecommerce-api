# Mini E-commerce API (FastAPI + Postgres + Redis + Celery)

A portfolio-ready backend that models a small e-commerce core:
catalog (products/categories), carts, orders, payments (Stripe checkout), webhooks, cache,
and background processing.

> This project is intentionally focused on **backend fundamentals**: correctness under concurrency,
clean boundaries, observable flows, and a testable architecture.

---

## Tech Stack

- **FastAPI** (REST API)
- **SQLAlchemy 2.x** + **Alembic** (migrations)
- **PostgreSQL** (primary DB)
- **Redis** (cache + Celery broker)
- **Celery** (background jobs)
- **Stripe SDK** (Checkout + Webhook) *(tests monkeypatch Stripe calls; no real payment required)*

---

## Core Features

### Catalog
- Categories (name/slug)
- Products with price, currency, stock, and `active` flag
- Product list supports **cursor pagination** (keyset pagination)

### Cart
- Create cart
- Add/remove/update cart items
- Cart totals (derived)

### Orders + Payments
- Checkout creates:
  - `orders` (status: `PENDING_PAYMENT` → `PAID` → `FULFILLED`)
  - `payments` (status: `INITIATED` → `SUCCEEDED` etc.)
  - Stripe Checkout Session (`stripe_session_id`)
- Webhook endpoint to mark a payment as succeeded (Stripe event)

### Cache (Redis)
- Cached “default” product listing first page (60s TTL)
- Safe invalidation when products change

### Background Tasks (Celery)
- Post-payment pipeline (`post_payment_pipeline`): after payment confirmation, marks the order as `FULFILLED`
- Cart expiration safety-net (`expire_cart_later`): after 30 minutes cancels pending orders and **releases reserved stock**

---

## Concurrency & Correctness (the important part)

### Stock reservation at checkout (prevents overselling)

The checkout flow reserves stock **inside a DB transaction** with **row-level locks**:

1. Load cart + items
2. `SELECT products ... FOR UPDATE` (locks the product rows)
3. Validate stock
4. Decrement stock (reserve)
5. Create order + payment
6. Commit

Because stock is decremented while holding the lock, two concurrent checkouts cannot oversell.

If the payment never completes:
- after ~30 minutes a Celery task cancels the pending order and restores the stock.

✅ This is the difference between “works on my machine” and “safe under concurrency”.

---

## Pagination

Product listing uses **cursor pagination** (keyset), which is faster and more stable than OFFSET for large tables.

**Endpoint**
- `GET /products?limit=20&after_id=123`

**Response**
```json
{
  "items": [ ... ],
  "next_cursor": 143
}
```

---

## Local Dev

### Requirements
- Docker + Docker Compose

### Run
```bash
docker compose up --build
```

API:
- http://localhost:8080
Docs:
- http://localhost:8080/docs

---

## Environment (.env)

Example:
```env
DATABASE_URL=postgresql+psycopg://app:app@db:5432/app
REDIS_URL=redis://redis:6379/0

STRIPE_API_KEY=sk_test_dummy
STRIPE_WEBHOOK_SECRET=
STRIPE_SUCCESS_URL=http://localhost:8080/payments/success
STRIPE_CANCEL_URL=http://localhost:8080/payments/cancel

# For local-only testing (do not use in prod)
ALLOW_INSECURE_WEBHOOK=true
```

---

## Testing

Tests prefer a real Postgres using **testcontainers** (recommended).

```bash
pytest -q
```

Included tests cover:
- cursor pagination (no duplicates between pages)
- checkout reservation under concurrency (two threads, one succeeds, one fails with insufficient stock)

---

## Project Layout

```
app/
  api/              # routers/controllers
  core/             # config + DB session
  models/           # SQLAlchemy models
  schemas/          # Pydantic schemas
  services/         # business logic (catalog/cart/checkout/payment)
  tasks/            # Celery tasks
alembic/            # migrations
tests/              # pytest suite
```

---

## “Should this have auth?”

Not required for a portfolio demo of backend fundamentals (catalog + carts + payments + concurrency).
If you want to push this to “production-like”, the next step is:
- JWT auth (users)
- carts bound to user_id
- role-based admin endpoints for product management

Keeping auth out of the base version keeps the focus on:
**DB modeling, correctness, and system behavior**.

---
