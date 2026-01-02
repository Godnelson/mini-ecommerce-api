import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

try:
    from testcontainers.postgres import PostgresContainer
    HAS_TC = True
except Exception:
    HAS_TC = False

from app.main import create_app
from app.core.db import get_db, init_db

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="session")
def pg_url():
    if not HAS_TC:
        pytest.skip("testcontainers not available")
    with PostgresContainer("postgres:16") as pg:
        url = pg.get_connection_url().replace("postgresql://", "postgresql+psycopg://")
        yield url

@pytest.fixture(scope="session")
def engine(pg_url):
    init_db(pg_url)
    eng = create_engine(pg_url, pool_pre_ping=True, future=True)
    # run migrations
    from alembic import command
    from alembic.config import Config
    import os
    cfg = Config("alembic.ini")
    os.environ["DATABASE_URL"] = pg_url
    command.upgrade(cfg, "head")
    return eng

@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def app(db_session):
    app = create_app()
    def _get_test_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_test_db
    return app

@pytest.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
