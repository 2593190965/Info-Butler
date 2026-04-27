import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 导入所有模型以确保 Base.metadata 包含所有表
import backend.models  # noqa: F401
from backend.core.base import Base
from backend.core.config import settings
from backend.main import app

# 使用 SQLite 内存数据库进行测试
SQLITE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    SQLITE_URL,
    echo=False,
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
async def setup_database():
    """创建测试数据库表"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database):
    """提供数据库会话"""
    async with test_session_maker() as session:
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
