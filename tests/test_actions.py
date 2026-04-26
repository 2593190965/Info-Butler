import pytest


@pytest.mark.anyio
async def test_list_actions(client):
    """测试获取行动项列表"""
    response = await client.get("/api/v1/actions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.anyio
async def test_list_actions_with_filter(client):
    """测试带筛选条件的行动项列表"""
    response = await client.get("/api/v1/actions?status=pending&priority=high")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.anyio
async def test_update_action_not_found(client):
    """测试更新不存在的行动项"""
    response = await client.patch(
        "/api/v1/actions/99999",
        json={"status": "done"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_batch_update_actions(client):
    """测试批量更新行动项状态"""
    response = await client.patch(
        "/api/v1/actions/batch",
        json={
            "ids": [1, 2, 3],
            "status": "done",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "updated_count" in data


@pytest.mark.anyio
async def test_batch_delete_actions(client):
    """测试批量删除行动项"""
    response = await client.delete(
        "/api/v1/actions/batch",
        json={"ids": [1, 2]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "deleted_count" in data
