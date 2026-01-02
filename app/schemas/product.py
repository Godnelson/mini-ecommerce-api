from pydantic import BaseModel

class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: str | None = None
    price_cents: int
    currency: str = "brl"
    stock: int = 0
    active: bool = True

class ProductPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    price_cents: int | None = None
    currency: str | None = None
    stock: int | None = None
    active: bool | None = None
    category_id: int | None = None

class ProductOut(BaseModel):
    id: int
    category_id: int
    name: str
    description: str | None
    price_cents: int
    currency: str
    stock: int
    active: bool

    class Config:
        from_attributes = True
