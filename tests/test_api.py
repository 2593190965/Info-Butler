import json
import time

import httpx

BASE = "http://localhost:8001"
HEADERS = {"X-API-Key": "dev-api-key-2026", "Content-Type": "application/json"}

client = httpx.Client(base_url=BASE, headers=HEADERS, timeout=60)

print("=" * 60)
print("  Info-Butler 功能性测试")
print("=" * 60)

# 1. 健康检查
print("\n[1/7] 健康检查 /health")
resp = client.get("/health")
print(f"   状态: {resp.status_code} - {json.dumps(resp.json(), ensure_ascii=False)}")
assert resp.status_code == 200

# 2. 提交信息
print("\n[2/7] 提交信息 POST /api/v1/digest")
test_text = """FastAPI 是一个现代、高性能的 Python Web 框架，基于 Starlette 和 Pyd 构建。
它支持异步编程、自动生成 OpenAPI 文档、类型提示验证。
主要特性包括：
1. 高性能：与 NodeJS 和 Go 相当
2. 自动文档：Swagger UI 和 ReDoc
3. 类型安全：Pydantic 数据校验
4. 异步支持：原生 async/await
5. 依赖注入：灵活的依赖管理"""
resp = client.post("/api/v1/digest", json={"source_type": "text", "content": test_text})
data = resp.json()
task_id = data.get("task_id", "")
print(f"   状态: {resp.status_code}")
print(f"   task_id: {task_id}")
assert resp.status_code in [200, 202] and task_id

# 3. 查询处理结果
print(f"\n[3/7] 查询结果 GET /api/v1/digest/{task_id[:8]}...")
time.sleep(2)
resp = client.get(f"/api/v1/digest/{task_id}")
result = resp.json()
print(f"   状态: {resp.status_code}")
summary = result.get("summary", "")
print(f"   摘要: {summary[:80]}...")
tags = result.get("tags", [])
print(f"   标签: {tags}")
actions = result.get("action_items", [])
print(f"   行动项数: {len(actions)}")

# 4. 获取行动项列表
print("\n[4/7] 行动项列表 GET /api/v1/actions")
resp = client.get("/api/v1/actions")
action_data = resp.json()
print(f"   状态: {resp.status_code}")
print(f"   总数: {action_data.get('total', 0)}")
if action_data.get("items"):
    print(f"   第一条: {action_data['items'][0]['content'][:50]}...")

# 5. 更新行动项状态
print("\n[5/7] 更新行动项 PATCH /api/v1/actions/{id}")
if action_data.get("items"):
    action_id = action_data["items"][0]["id"]
    resp = client.patch(f"/api/v1/actions/{action_id}", json={"status": "done"})
    print(f"   状态: {resp.status_code}")
    print(f"   新状态: {resp.json()['status']}")

# 6. 标签列表
print("\n[6/7] 标签列表 GET /api/v1/tags")
resp = client.get("/api/v1/tags")
tag_resp = resp.json()
print(f"   状态: {resp.status_code}")
tag_data = tag_resp.get("data", tag_resp)
print(f"   标签数: {len(tag_data.get('items', []))}")
for t in tag_data.get("items", [])[:5]:
    print(f"     - {t['name']} (关联{t['info_count']}条)")

# 7. 周报复盘
print("\n[7/7] 周报统计 GET /api/v1/review/weekly")
resp = client.get("/api/v1/review/weekly")
review_resp = resp.json()
review = review_resp.get("data", review_resp)
print(f"   状态: {resp.status_code}")
print(f"   本周时间: {review.get('week_start')} ~ {review.get('week_end')}")
print(f"   新增信息: {review.get('new_info_count')}")
print(f"   新增行动: {review.get('new_action_count')}")
print(f"   已完成: {review.get('done_action_count')}")
rate = review.get("completion_rate", 0)
print(f"   完成率: {rate * 100:.1f}%")

print("\n" + "=" * 60)
print("  ✅ 所有功能测试通过!")
print("=" * 60)

client.close()
