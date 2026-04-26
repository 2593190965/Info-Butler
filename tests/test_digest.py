import pytest


@pytest.mark.anyio
async def test_create_digest_text(client):
    """测试创建文本类型知识卡片"""
    response = await client.post(
        "/api/v1/digest",
        json={
            "source_type": "text",
            "content": "这是一个测试内容",
            "title": "测试标题",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "processing"


@pytest.mark.anyio
async def test_create_digest_invalid_type(client):
    """测试无效来源类型"""
    response = await client.post(
        "/api/v1/digest",
        json={
            "source_type": "invalid",
            "content": "测试内容",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_digest_empty_content(client):
    """测试空内容"""
    response = await client.post(
        "/api/v1/digest",
        json={
            "source_type": "text",
            "content": "",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_digests(client):
    """测试获取知识卡片列表"""
    response = await client.get("/api/v1/digest")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.anyio
async def test_list_digests_with_filter(client):
    """测试带筛选条件的列表查询"""
    response = await client.get("/api/v1/digest?status=done&keyword=test")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.anyio
async def test_get_digest_not_found(client):
    """测试获取不存在的知识卡片"""
    response = await client.get("/api/v1/digest/non-existent-id")
    assert response.status_code == 404
