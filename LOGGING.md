# Info-Butler 日志配置指南

## 📋 日志说明

### 启动时看到的日志

#### 1. 数据库连接日志（正常）
```
SELECT DATABASE()
SELECT @@sql_mode
SELECT @@lower_case_table_names
DESCRIBE `info_butler`.`action_items`
...
```

**含义：**
- SQLAlchemy 启动时验证数据库结构
- 确保所有表存在且结构正确
- **这是正常的健康检查，不是错误**

**是否需要关注：** ❌ 不需要，这是正常的启动流程

---

#### 2. API 请求日志（正常）
```
BEGIN (implicit)
SELECT rss_subscriptions...
INFO: 127.0.0.1:8944 - "GET /api/v1/rss HTTP/1.1" 200 OK
ROLLBACK
```

**含义：**
- 用户请求 API
- 数据库开启事务
- 查询数据并返回
- **这是正常的业务流程**

**是否需要关注：** ❌ 不需要，除非看到大量 ERROR

---

#### 3. RSS 抓取失败（需要关注）
```
No entries found for RSS feed: https://...
UPDATE rss_subscriptions SET last_fetch_status='failed'
```

**含义：**
- RSS URL 不是有效的 RSS 源
- 可能是具体的文章链接而非 RSS 源

**是否需要关注：** ⚠️ 需要，检查 RSS URL 是否正确

---

## 🎛️ 日志级别配置

### 方法 1：通过 .env 文件配置（推荐）

在项目根目录的 `.env` 文件中添加：

```env
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

#### 日志级别说明

| 级别 | 显示内容 | 适用场景 |
|------|---------|----------|
| **DEBUG** | 所有详细信息，包括 SQL 语句 | 🔍 开发调试 |
| **INFO** | 关键操作信息（默认） | ✅ 日常开发 |
| **WARNING** | 仅警告和错误 | 🚀 生产环境 |
| **ERROR** | 仅错误信息 | 🔧 故障排查 |
| **CRITICAL** | 仅严重错误 | 🏭 生产环境 |

---

### 方法 2：通过环境变量配置

**Windows PowerShell：**
```powershell
$env:LOG_LEVEL="WARNING"
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

**Linux/Mac：**
```bash
LOG_LEVEL=WARNING uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

---

### 方法 3：临时查看详细日志

如果需要调试某个问题，可以临时开启 DEBUG 级别：

```bash
# 方法 1：修改 .env
LOG_LEVEL=DEBUG

# 方法 2：环境变量
LOG_LEVEL=DEBUG uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

---

## 📊 已优化的日志输出

### ✅ 已屏蔽的冗余日志

在 `backend/main.py` 中已配置：

```python
# 屏蔽 SQLAlchemy 引擎的详细 SQL 日志
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)

# 减少访问日志
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
```

**效果：**
- ✅ 不再显示每条 SQL 的执行时间
- ✅ 不再显示数据库连接细节
- ✅ 保留关键的错误和警告信息

---

## 🔍 日志分析示例

### 正常启动日志（优化后）

```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
INFO:     127.0.0.1:8944 - "GET /api/v1/rss HTTP/1.1" 200 OK
```

### 异常日志（需要关注）

```
ERROR - Failed to connect to database
ERROR - RSS fetch failed: timeout
WARNING - Redis connection failed
```

---

## 🛠️ 实用技巧

### 1. 查看最近的错误日志

**Linux/Mac：**
```bash
# 查看最近 50 行错误日志
uv run uvicorn backend.main:app 2>&1 | grep -i error | tail -50
```

**Windows PowerShell：**
```powershell
# 将日志保存到文件
uv run uvicorn backend.main:app 2>&1 | Tee-Object -FilePath logs.txt

# 然后在 VS Code 中搜索 "ERROR"
```

---

### 2. 监控特定模块的日志

如果想看特定模块的日志（例如 RSS 抓取）：

```python
# 临时启用 RSS 模块的 DEBUG 日志
import logging
logging.getLogger("backend.services.rss_service").setLevel(logging.DEBUG)
```

---

### 3. 生产环境日志配置

**.env（生产环境）：**
```env
LOG_LEVEL=WARNING
DEBUG=false
```

**效果：**
- ✅ 只记录警告和错误
- ✅ 减少日志文件大小
- ✅ 提高性能

---

## 🎯 常见问题

### Q1: 为什么启动时有这么多数据库日志？

**A:** 这是 SQLAlchemy 的正常行为：
- 启动时验证所有表结构
- 确保数据库连接正常
- 已通过日志配置屏蔽了大部分冗余信息

---

### Q2: 如何判断日志是否正常？

**A:** 看日志级别：

| 级别 | 状态 |
|------|------|
| INFO | ✅ 正常 |
| WARNING | ⚠️ 需要关注但不影响运行 |
| ERROR | ❌ 需要修复 |

---

### Q3: 日志太多影响性能怎么办？

**A:** 调整日志级别：

```env
# 生产环境配置
LOG_LEVEL=WARNING
DEBUG=false
```

---

### Q4: 如何只看 API 请求日志？

**A:** 使用 uvicorn 的访问日志：

```bash
# 只看访问日志
uv run uvicorn backend.main:app --log-level info 2>&1 | grep "GET\|POST\|PUT\|DELETE"
```

---

## 📝 日志最佳实践

### 开发环境
```env
LOG_LEVEL=INFO
DEBUG=true
```

### 生产环境
```env
LOG_LEVEL=WARNING
DEBUG=false
```

### 调试问题
```env
LOG_LEVEL=DEBUG
DEBUG=true
```

---

## 🔗 相关文件

- 日志配置：`backend/main.py`
- 配置文件：`backend/core/config.py`
- 环境变量：`.env`

---

需要更多帮助？查看 [README.md](./README.md) 或提交 Issue。
