import pytest
import pytest_asyncio
import httpx
from app.core.database import init_db, close_db
from app.core.redis import cache_service
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_test_environment():
    await init_db()
    await cache_service.initialize()
    await cache_service.clear()
    yield
    await cache_service.clear()
    await cache_service.close()
    await close_db()


@pytest_asyncio.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
