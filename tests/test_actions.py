import pytest


@pytest.mark.asyncio
async def test_list_actions_empty(client):
    resp = await client.get("/api/v1/actions")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
