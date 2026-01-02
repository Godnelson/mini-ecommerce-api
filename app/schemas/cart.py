from pydantic import BaseModel

class CartCreateOut(BaseModel):
    id: int
    status: str

class CartItemAdd(BaseModel):
    product_id: int
    qty: int

class CartItemPatch(BaseModel):
    qty: int

class CartItemOut(BaseModel):
    id: int
    product_id: int
    qty: int
    unit_price_cents: int

    class Config:
        from_attributes = True

class CartOut(BaseModel):
    id: int
    status: str
    items: list[CartItemOut]
    total_cents: int
    currency: str
