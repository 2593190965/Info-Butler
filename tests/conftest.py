import pytest
from httpx import ASGITransport, AsyncClient

from backend.core.base import Base
from backend.core.config import settings
from backend.core.database import async_session, engine
from backend.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def setup_database():
    """创建测试数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database):
    """提供数据库会话"""
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(setup_database):
    """提供 HTTP 测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-API-Key": settings.api_key},
    ) as ac:
        yield ac
