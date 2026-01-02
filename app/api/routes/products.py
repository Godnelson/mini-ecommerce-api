from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductPatch, ProductOut
from app.services.catalog_service import list_products, get_product, invalidate_product_cache

router = APIRouter(prefix="/products")

@router.get("", response_model=dict)
def list_(
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    after_id: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """Cursor-paginated product listing.

    Example:
      /products?limit=20
      /products?limit=20&after_id=40
    """
    return list_products(db, category, q, limit=limit, after_id=after_id)

@router.get("/{product_id}", response_model=dict)
def get_(product_id: int, db: Session = Depends(get_db)):
    p = get_product(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

@router.post("", response_model=ProductOut, status_code=201)
def create(payload: ProductCreate, db: Session = Depends(get_db)):
    p = Product(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    invalidate_product_cache(p.id)
    return p

@router.patch("/{product_id}", response_model=ProductOut)
def patch(product_id: int, payload: ProductPatch, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    data = payload.model_dump(exclude_unset=True)
    for k,v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    invalidate_product_cache(p.id)
    return p
