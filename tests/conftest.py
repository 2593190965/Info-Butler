import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-API-Key": "dev-api-key-2026"},
    ) as ac:
        yield ac
