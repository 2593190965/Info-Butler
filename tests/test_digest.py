import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_create_digest_text(client):
    payload = {
        "source_type": "text",
        "content": (
            "FastAPI is a modern, fast (high-performance), web framework "
            "for building APIs with Python 3.8+ based on standard Python type hints."
        ),
    }
    resp = await client.post("/api/v1/digest", json=payload)
    assert resp.status_code in (200, 202)
    data = resp.json()
    assert "task_id" in data.get("data", {})
