from fastapi import APIRouter
from app.api.routes.categories import router as categories_router
from app.api.routes.products import router as products_router
from app.api.routes.cart import router as cart_router
from app.api.routes.checkout import router as checkout_router
from app.api.routes.orders import router as orders_router
from app.api.routes.webhooks import router as webhooks_router

router = APIRouter()
router.include_router(categories_router, tags=["categories"])
router.include_router(products_router, tags=["products"])
router.include_router(cart_router, tags=["cart"])
router.include_router(checkout_router, tags=["checkout"])
router.include_router(orders_router, tags=["orders"])
router.include_router(webhooks_router, tags=["webhooks"])
