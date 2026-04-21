# Info-Butler

智能信息管家 - 自动整理信息、提取行动项、生成周报复盘

## 功能特性

- **信息摘要**: 输入文本或 URL，自动生成结构化摘要
- **行动项提取**: 智能识别可执行的任务，按优先级分类
- **标签管理**: 自动打标签，支持按标签筛选
- **周报复盘**: 一键生成本周统计报告

## 技术栈

- **后端**: FastAPI + SQLAlchemy (async)
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **AI**: Dify Workflow
- **包管理**: uv

## 环境要求

- Python 3.12+
- MySQL 8.0+
- Redis
- Dify (已配置 Workflow)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Info-Butler
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 应用配置
APP_NAME=Info-Butler
APP_ENV=development
DEBUG=true
API_KEY=your-api-key-here

# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=info_butler

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=1

# Dify 配置
DIFY_API_URL=http://localhost/v1
DIFY_API_KEY=your-dify-api-key
DIFY_WORKFLOW_ID=your-workflow-id
```

### 4. 创建数据库

```sql
CREATE DATABASE info_butler CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 启动服务

```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

服务启动后访问：
- API 文档: http://localhost:8001/docs
- 健康检查: http://localhost:8001/health

## API 使用示例

### 提交信息

```bash
curl -X POST http://localhost:8001/api/v1/digest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "source_type": "text",
    "content": "FastAPI 是一个现代、高性能的 Python Web 框架..."
  }'
```

响应：
```json
{
  "task_id": "uuid-here",
  "status": "done"
}
```

### 查询处理结果

```bash
curl http://localhost:8001/api/v1/digest/{task_id} \
  -H "X-API-Key: your-api-key"
```

响应：
```json
{
  "id": 1,
  "task_id": "uuid-here",
  "summary": "信息摘要...",
  "tags": ["Python", "Web框架", "API开发"],
  "action_items": [
    {"id": 1, "content": "阅读官方文档", "status": "pending", "priority": "medium"}
  ],
  "status": "done"
}
```

### 获取行动项列表

```bash
curl "http://localhost:8001/api/v1/actions?status=pending" \
  -H "X-API-Key: your-api-key"
```

### 更新行动项状态

```bash
curl -X PATCH http://localhost:8001/api/v1/actions/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"status": "done"}'
```

### 获取周报

```bash
curl http://localhost:8001/api/v1/review/weekly \
  -H "X-API-Key: your-api-key"
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/digest` | 提交信息（文本/URL） |
| GET | `/api/v1/digest` | 知识卡片列表 |
| GET | `/api/v1/digest/{task_id}` | 查询处理结果 |
| GET | `/api/v1/actions` | 行动项列表 |
| PATCH | `/api/v1/actions/{id}` | 更新行动项 |
| PATCH | `/api/v1/actions/batch` | 批量更新行动项 |
| GET | `/api/v1/tags` | 标签列表 |
| GET | `/api/v1/review/weekly` | 周报统计 |
| GET | `/health` | 健康检查 |

## Dify Workflow 配置

在 Dify 中创建 Workflow，需要以下输入/输出：

**输入变量：**
- `input_text` (string): 待处理的文本内容
- `source_type` (string): 来源类型 (text/url)

**输出变量：**
- `summary` (string): 信息摘要
- `action_items` (array): 行动项列表
  ```json
  [{"content": "任务内容", "priority": "high|medium|low"}]
  ```
- `tags` (array): 标签列表
  ```json
  ["标签1", "标签2", "标签3"]
  ```

## 项目结构

```
Info-Butler/
├── backend/
│   ├── api/           # API 路由
│   ├── clients/       # 外部服务客户端
│   ├── core/          # 核心配置
│   ├── models/        # ORM 模型
│   ├── schemas/       # Pydantic 模型
│   ├── services/      # 业务逻辑
│   └── main.py        # 入口文件
├── alembic/           # 数据库迁移
├── tests/             # 测试文件
├── .env               # 环境变量
├── pyproject.toml     # 项目配置
└── README.md
```

## 开发

### 运行测试

```bash
uv run pytest
```

### 代码检查

```bash
uv run ruff check backend/
```

### 数据库迁移

```bash
# 生成迁移脚本
uv run alembic revision --autogenerate -m "description"

# 执行迁移
uv run alembic upgrade head
```

## License

MIT
