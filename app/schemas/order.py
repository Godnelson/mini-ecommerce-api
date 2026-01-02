from pydantic import BaseModel

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    qty: int
    unit_price_cents: int

    class Config:
        from_attributes = True

class PaymentOut(BaseModel):
    status: str
    provider: str
    amount_cents: int
    currency: str
    stripe_session_id: str | None

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    cart_id: int
    total_cents: int
    currency: str
    status: str
    items: list[OrderItemOut]
    payment: PaymentOut | None

    class Config:
        from_attributes = True

class CheckoutOut(BaseModel):
    order_id: int
    session_id: str
    checkout_url: str
