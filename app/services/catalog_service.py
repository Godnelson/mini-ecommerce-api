from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product
from app.services.utils import slugify
from app.core.cache import cache_get_json, cache_set_json, cache_del

PRODUCT_LIST_KEY = "products:list"
PRODUCT_KEY_PREFIX = "product:"

def list_products(
    db: Session,
    category_slug: str | None,
    q: str | None,
    *,
    limit: int = 20,
    after_id: int | None = None,
) -> dict:
    """List products with **cursor pagination** (keyset).

    - Stable order: by Product.id ASC
    - Cursor: last returned `id` (`after_id` param)
    """
    # Normalize / guardrails
    limit = max(1, min(int(limit), 100))

    # Cache only for the "default first page" (no filters, no cursor)
    cacheable = (not category_slug and not q and after_id is None and limit == 20)
    if cacheable:
        cached = cache_get_json(PRODUCT_LIST_KEY)
        if cached is not None:
            return cached

    query = db.query(Product).filter(Product.active.is_(True))
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if after_id is not None:
        query = query.filter(Product.id > after_id)

    # Fetch one extra to know if there's a next page
    items = query.order_by(Product.id.asc()).limit(limit + 1).all()
    has_more = len(items) > limit
    items = items[:limit]

    result_items = [serialize_product(p) for p in items]
    next_cursor = items[-1].id if (has_more and items) else None

    result = {"items": result_items, "next_cursor": next_cursor}

    if cacheable:
        cache_set_json(PRODUCT_LIST_KEY, result, ttl_seconds=60)

    return result

def get_product(db: Session, product_id: int):
    key = f"{PRODUCT_KEY_PREFIX}{product_id}"
    cached = cache_get_json(key)
    if cached is not None:
        return cached
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return None
    data = serialize_product(p)
    cache_set_json(key, data, ttl_seconds=120)
    return data

def create_category(db: Session, name: str) -> Category:
    slug = slugify(name)
    c = Category(name=name, slug=slug)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def invalidate_product_cache(product_id: int | None = None):
    keys = [PRODUCT_LIST_KEY]
    if product_id is not None:
        keys.append(f"{PRODUCT_KEY_PREFIX}{product_id}")
    cache_del(*keys)

def serialize_product(p: Product):
    return {
        "id": p.id,
        "category_id": p.category_id,
        "name": p.name,
        "description": p.description,
        "price_cents": p.price_cents,
        "currency": p.currency,
        "stock": p.stock,
        "active": p.active,
    }
