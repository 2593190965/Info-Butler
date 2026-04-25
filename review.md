# Info-Butler 代码审查报告

> 审查日期: 2026-04-25
> 审查范围: 全项目（后端 Python + 前端 Vue 3）
> 审查方式: 安全审查 + Python 代码审查 + 静默失败审查（三路并行）

---

## CRITICAL（4 个）— 必须修复

### C1. 标签创建竞态条件 + 缺少回滚 → 数据损坏

- **位置**: `backend/services/digest_service.py:73-80, 113-136`
- **问题**: 两个并发请求处理含有相同标签的 digest 时，都会通过 `scalar_one_or_none()` 检查并尝试插入同一标签，第二个触发 `IntegrityError`。异常处理器直接 `commit()`，没有先 `rollback()`，导致已 flush 的部分数据（标签、关联表）和 "failed" 状态一起被提交，数据库处于不一致状态。
- **修复**: 异常处理器中先 `rollback()`，再用 `INSERT ... ON DUPLICATE KEY` 或捕获 `IntegrityError` 后重新查询标签。

### C2. 批量导入静默吞噬所有异常 → 永久僵尸记录

- **位置**: `backend/api/v1/tasks.py:39-42`
- **问题**: `except Exception: pass` 吞掉所有错误，`raw_info` 已以 `"processing"` 状态写入数据库但永远不会更新。用户看到 "提交成功"，实际所有条目全部失败且永远卡在 processing。
- **修复**: 移除 `except Exception: pass`，记录错误并设置 `raw_info.status = "failed"`，收集每项错误返回给用户。

### C3. Dify 响应不完整时注入虚假数据

- **位置**: `backend/clients/dify_client.py:119-126`
- **问题**: AI 返回不足 3 个标签时自动填充 `tag-1`、`tag-2` 等虚假标签；无行动项时注入 "Review the original content"。这些假数据被持久化到数据库，用户无法区分真假。
- **修复**: 不注入虚假数据，当 AI 响应不足时设置 `status = "parse_error"` 并明确告知用户。

### C4. 无 stuck-in-processing 恢复机制

- **位置**: `backend/workers/worker_settings.py:29-30`、`backend/workers/tasks.py`、`backend/services/digest_service.py`
- **问题**: ARQ worker 崩溃、Redis 丢任务、错误处理器自身失败时，记录永久卡在 `"processing"`。`on_job_failure` 只打日志不更新数据库状态。无超时清理、无管理端点、无回收机制。
- **修复**: (1) `on_job_failure` 中更新 `raw_info.status = "failed"`；(2) 添加定时任务/管理端点，将超过 30 分钟仍在 processing 的记录标记为超时；(3) 异常处理器中的 `commit` 也用 try/except 包裹。

---

## HIGH（9 个）— 强烈建议修复

### H1. API Key 认证硬编码 user_id=1 → 数据隔离被打破

- **位置**: `backend/api/deps.py:11-12`
- **问题**: 所有 API Key 请求都映射到 user_id=1，可访问该用户所有数据。
- **修复**: 将 API Key 与特定用户 ID 关联，或在多用户环境下拒绝 API Key 认证。

### H2. SSRF 漏洞 — URL 抓取无任何校验

- **位置**: `backend/clients/scraper_client.py:97-98`
- **问题**: 用户可提交 `http://169.254.169.254/`（AWS 元数据）、`http://localhost:6379/`（Redis）等内部地址，服务器会直接请求。`follow_redirects=True` 加剧了风险。
- **修复**: 阻止私有/保留 IP 段（10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16），仅允许 http/https 协议。

### H3. 硬编码默认 JWT Secret → Token 伪造

- **位置**: `backend/core/config.py:9`
- **问题**: 默认值 `info-butler-jwt-secret-key-change-in-production-2026` 可被任何人猜到，无启动校验。
- **修复**: 生产环境启动时校验 JWT Secret 已被更改，否则拒绝启动。

### H4. 周回顾日期 off-by-one bug

- **位置**: `backend/services/review_service.py:23-29`
- **问题**: `end` 是 `date` 对象（如 2024-01-07），MySQL 解释为 `00:00:00`，导致当天所有记录被排除。
- **修复**: 使用 `end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time())` 并过滤 `created_at < end_dt`。

### H5. 标签列表 N+1 查询问题

- **位置**: `backend/services/tag_service.py:27-43`
- **问题**: 每个标签执行 2 次额外查询，50 个标签 = 100 次查询，高并发下会打满连接池。
- **修复**: 使用 `GROUP BY` 聚合查询一次获取所有计数。

### H6. ARQ 重试导致重复数据

- **位置**: `backend/workers/tasks.py` + `backend/services/digest_service.py`
- **问题**: `max_tries=3` 时，已部分提交的数据在重试时不会被清理，产生重复 action_items 和关联。
- **修复**: `process_digest_sync` 开始时检查 `raw_info.status`，若已 "failed" 或 "done" 则跳过或先清理部分数据。

### H7. Redis 不可用导致整个应用无法启动

- **位置**: `backend/main.py:29`
- **问题**: 启动时 `await get_arq_pool()` 失败会阻止 FastAPI 启动，即使只有读操作也不可用。
- **修复**: 用 try/except 包裹，允许应用启动但记录警告，在实际入队时才报错。

### H8. 前端 API 失败显示空状态，无错误提示

- **位置**: `DigestList.vue:112-113`、`Actions.vue:113-114`、`Tags.vue:133-134`、`Review.vue:77-78`
- **问题**: 全部用 `console.error` 吞掉错误，用户看到 "暂无数据" 而非错误提示。
- **修复**: 在 catch 中设置错误状态 ref，在模板中显示错误信息或 `message.error()` 通知。

### H9. DifyClient 重试逻辑捕获所有异常

- **位置**: `backend/clients/dify_client.py:45`
- **问题**: `except (HTTPStatusError, Exception)` 会对编程错误（TypeError、KeyError）也重试 3 次，浪费时间。
- **修复**: 仅捕获瞬态异常（`httpx.ConnectError`、`httpx.TimeoutException`、5xx `HTTPStatusError`），编程错误直接抛出。

---

## MEDIUM（8 个）— 建议修复

### M1. 周回顾 week_start 参数无格式校验

- **位置**: `backend/services/review_service.py:16`
- **问题**: `date.fromisoformat(week_start)` 对非法输入抛 ValueError，导致 500 而非 422。
- **修复**: 使用 Pydantic 模型或 `Query` 参数加正则校验。

### M2. LIKE 搜索通配符未转义

- **位置**: `backend/services/digest_service.py:162`、`backend/services/tag_service.py:17`
- **问题**: `keyword=%` 匹配所有行，`keyword=_` 匹配任意单字符，可绕过搜索意图。
- **修复**: 转义 LIKE 通配符：`keyword.replace("%", "\\%").replace("_", "\\_")`。

### M3. BatchActionUpdate.ids 无长度限制

- **位置**: `backend/schemas/action_item.py:31`
- **问题**: 可提交数千 ID，生成巨大 `IN (...)` SQL 子句。
- **修复**: 添加 `max_length=100` 约束。

### M4. Redis URL 构建未转义特殊字符密码

- **位置**: `backend/core/config.py:37-39`
- **问题**: 密码含 `@`、`:` 等字符时 URL 解析错误。
- **修复**: 使用 `urllib.parse.quote` 转义密码，或直接使用 `RedisSettings` 参数。

### M5. ScraperClient.close() 是空操作

- **位置**: `backend/clients/scraper_client.py:177-178`
- **问题**: ThreadPoolExecutor 和 httpx 资源不会被清理。
- **修复**: 实现 `_executor.shutdown(wait=False)` 和相关资源清理。

### M6. asyncio.get_event_loop() 已弃用

- **位置**: `backend/clients/scraper_client.py:172`
- **问题**: Python 3.10+ 中已弃用，应使用 `get_running_loop()`。
- **修复**: 替换为 `asyncio.get_running_loop()`。

### M7. 存储型 XSS — source_url 未校验 javascript: 协议

- **位置**: `frontend/src/views/DigestDetail.vue:12`
- **问题**: `<a :href="data.source_url">` 未过滤 `javascript:` URI，可执行任意 JS。
- **修复**: 后端校验 `source_url` 必须以 `http://` 或 `https://` 开头；前端添加协议校验。

### M8. 前端硬编码 API Key 回退值

- **位置**: `frontend/src/api/index.ts:18`
- **问题**: `import.meta.env.VITE_API_KEY || 'dev-api-key-2026'` 在生产环境暴露开发密钥。
- **修复**: 移除硬编码回退值，未配置时发送 401 响应触发登录。

---

## 修复状态

> 修复完成时间: 2026-04-25

| ID | 状态 | 修复文件 |
|----|------|----------|
| C1 | ✅ 已修复 | `backend/services/digest_service.py` - 使用 `INSERT ... ON DUPLICATE KEY`，异常处理器添加 `rollback()` |
| C2 | ✅ 已修复 | `backend/api/v1/tasks.py` - 移除 `except: pass`，记录错误并设置失败状态 |
| C3 | ✅ 已修复 | `backend/clients/dify_client.py` - 移除虚假标签/行动项注入 |
| C4 | ✅ 已修复 | `backend/workers/worker_settings.py`, `backend/workers/tasks.py`, `backend/services/digest_service.py`, `backend/main.py` - 添加 `on_job_failure` 状态更新、超时清理机制 |
| H1 | ✅ 已修复 | `backend/api/deps.py`, `backend/core/config.py` - 添加 `api_key_user_id` 配置项 |
| H2 | ✅ 已修复 | `backend/clients/scraper_client.py` - 阻止私有 IP 段、校验 URL 协议 |
| H3 | ✅ 已修复 | `backend/core/config.py` - 生产环境启动时校验 JWT Secret |
| H4 | ✅ 已修复 | `backend/services/review_service.py` - 修复日期比较逻辑 |
| H5 | ✅ 已修复 | `backend/services/tag_service.py` - 使用 `GROUP BY` 聚合查询 |
| H6 | ✅ 已修复 | `backend/workers/tasks.py` - 检查 `raw_info.status` 跳过已完成任务 |
| H7 | ✅ 已修复 | `backend/main.py` - 用 try/except 包裹 ARQ 池初始化 |
| H8 | ✅ 已修复 | `DigestList.vue`, `Actions.vue`, `Tags.vue`, `Review.vue`, `DigestDetail.vue` - 添加错误提示 |
| H9 | ✅ 已修复 | `backend/clients/dify_client.py` - 仅重试瞬态异常 |
| M1 | ✅ 已修复 | `backend/services/review_service.py` - 添加日期格式校验 |
| M2 | ✅ 已修复 | `backend/services/digest_service.py`, `backend/services/tag_service.py` - LIKE 通配符转义 |
| M3 | ✅ 已修复 | `backend/schemas/action_item.py` - 添加 `max_length=100` |
| M4 | ✅ 已修复 | `backend/core/config.py` - URL 编码密码 |
| M5 | ✅ 已修复 | `backend/clients/scraper_client.py` - 实现 `close()` 方法 |
| M6 | ✅ 已修复 | `backend/clients/scraper_client.py` - 使用 `get_running_loop()` |
| M7 | ✅ 已修复 | `backend/api/v1/digest.py`, `backend/api/v1/tasks.py`, `frontend/src/views/DigestDetail.vue` - URL 协议校验 |
| M8 | ✅ 已修复 | `frontend/src/api/index.ts` - 移除硬编码回退值 |

**所有 21 个问题已全部修复。**

### 额外修复

- `backend/core/security.py` - 使用 `hmac.compare_digest()` 防止时序攻击
- `backend/core/security.py` - JWT 解码失败时添加日志
- `backend/models/action_item.py`, `backend/models/tag.py` - 修复行长度 lint 错误
- `backend/clients/dify_client.py` - 修复模糊变量名 lint 错误
