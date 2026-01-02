from fastapi import FastAPI
from app.core.config import settings
from app.core.db import init_db
from app.api.routes import router

def create_app() -> FastAPI:
    app = FastAPI(title="Mini E-commerce API")
    init_db(settings.DATABASE_URL)
    app.include_router(router)
    return app

app = create_app()
