# Info-Butler

智能信息管家 - 自动整理信息、提取行动项、生成周报复盘

## 功能特性

### 核心功能

| 功能 | 说明 |
|------|------|
| **信息录入** | 支持文本和 URL 两种输入方式，自动抓取 URL 内容，可选择是否生成行动项和标签 |
| **AI 摘要生成** | 调用 Dify Workflow 自动生成结构化摘要 |
| **行动项提取** | 智能识别可执行任务，按 high/medium/low 优先级分类 |
| **自动标签** | AI 生成 3-5 个标签，支持 CRUD 管理 |
| **知识卡片库** | 分页浏览、全文搜索（MySQL FULLTEXT）、状态筛选、批量管理（删除/归档/添加标签）、关键词高亮 |
| **行动项看板** | 三栏看板（待办 / 已完成 / 已忽略），支持状态切换、到期/逾期标记、批量操作（删除/改优先级/添加标签） |
| **周复查仪表盘** | 可视化图表展示（30天趋势、标签分布、全局统计），数字卡片动画效果 |
| **飞书通知** | 处理完成/失败时自动推送飞书群消息（摘要+行动项） |
| **标签管理** | 独立管理页面，支持 CRUD + 搜索 + 关联统计 + 批量操作（删除/合并） |
| **信息详情** | 点击卡片查看完整内容，行动项状态可切换，关联推荐（基于共享标签） |
| **标签筛选** | 列表页点击标签快速按名称筛选信息 |
| **JWT 认证** | 用户注册/登录，Bearer Token 鉴权，7天有效期 |
| **数据隔离** | 所有数据（卡片/标签/行动项/周报）按用户完全独立 |
| **批量导入** | 一次提交最多20条信息，支持文本和URL |
| **队列监控** | 实时查看处理状态（待处理/完成/失败） |
| **数据导出** | 支持 Markdown/JSON/CSV 格式导出知识卡片和行动项 |
| **提醒系统** | 行动项到期/逾期视觉标记（橙色/红色边框）+ 时间标签 |
| **密码强度校验** | 注册时要求最少8位，含大小写字母+数字 |
| **JWT Token 黑名单** | 退出登录后 Token 立即失效 |
| **CORS 配置** | 支持通过环境变量控制允许的域名 |
| **安全响应头** | CSP、HSTS、X-Frame-Options 等防护 |
| **文件上传解析** | 支持 PDF/Word/Excel/TXT/Markdown 拖拽上传，自动触发 AI 处理 |
| **RSS 订阅** | RSS 源订阅管理，自动抓取文章并 AI 处理，前端网格展示 |
| **飞书双向集成** | 接收飞书机器人消息自动处理，返回摘要/行动项/标签 |

### 技术特性

- **异步处理**: ARQ 任务队列 + Redis，Dify 调用不阻塞请求
- **URL 抓取**: readability-lxml 提取网页正文内容
- **飞书机器人**: Webhook 实时通知，处理结果即时推送
- **全局异常处理**: 统一错误响应格式
- **API Key 鉴权**: 简单安全的接口保护
- **深色主题**: Naive UI Catppuccin 风格前端

## 技术栈

| 层 | 技术 |
|----|------|
| **后端框架** | FastAPI (async) |
| **ORM** | SQLAlchemy (async) + Alembic 迁移 |
| **数据验证** | Pydantic v2 |
| **数据库** | MySQL 8.0 |
| **缓存 / 队列** | Redis (DB 1) + ARQ |
| **AI 引擎** | Dify Workflow |
| **前端框架** | Vue 3.5 + Vite 6 |
| **UI 组件库** | Naive UI 2 (深色主题) |
| **HTTP 客户端** | Axios |
| **包管理** | uv (后端) + npm (前端) |
| **文件解析** | python-docx / openpyxl / pdfplumber |
| **RSS 解析** | feedparser |

## 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+
- Redis 7.0+
- Dify（已配置 Workflow）

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Info-Butler
```

### 2. 后端 - 安装依赖 & 配置

```bash
uv sync
```

复制 `.env.example` 为 `.env` 并填入配置：

```env
# 应用配置
APP_NAME=Info-Butler
APP_ENV=development
DEBUG=true
API_KEY=dev-api-key-2026

# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=info_butler
MYSQL_PASSWORD=butler_pass
MYSQL_DATABASE=info_butler

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=1

# Dify 配置
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-xxxxxxxxxxxxxxx
DIFY_WORKFLOW_ID=your-workflow-id

# 飞书机器人（可选）
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id
```

### 3. 前端 - 安装依赖

```bash
cd frontend && npm install
```

### 4. 启动服务

**终端 1 - 后端:**
```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

**终端 2 - ARQ Worker（生产环境需要单独启动）:**
```bash
uv run python -m backend.workers.run_worker
```

**终端 3 - 前端:**
```bash
cd frontend && npm run dev
```

访问地址：
| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5175 |
| API 文档 (Swagger) | http://localhost:8001/docs |
| 健康检查 | http://localhost:8001/health |

## API 端点

### 信息录入

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/digest` | 提交信息（文本/URL），返回 task_id，支持可选生成行动项和标签 |
| GET | `/api/v1/digest` | 知识卡片列表（分页、全文搜索、状态筛选） |
| GET | `/api/v1/digest/{task_id}` | 查询处理结果 |
| GET | `/api/v1/digest/{task_id}/related` | 关联推荐（基于共享标签） |
| DELETE | `/api/v1/digest/batch` | 批量删除知识卡片 |
| PATCH | `/api/v1/digest/batch/status` | 批量修改状态 |
| POST | `/api/v1/digest/batch/tags` | 批量添加标签 |

### 行动项

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/actions` | 行动项列表（支持 status/priority 筛选） |
| PATCH | `/api/v1/actions/{id}` | 更新单个行动项状态 |
| PATCH | `/api/v1/actions/batch` | 批量更新行动项状态 |
| DELETE | `/api/v1/actions/batch` | 批量删除行动项 |
| PATCH | `/api/v1/actions/batch/priority` | 批量修改优先级 |
| POST | `/api/v1/actions/batch/tags` | 批量添加标签 |

### 标签管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/tags` | 标签列表（分页、搜索） |
| POST | `/api/v1/tags` | 创建标签（自动去重） |
| PUT | `/api/v1/tags/{id}` | 更新标签名称 |
| DELETE | `/api/v1/tags/{id}` | 删除标签（清理关联） |
| DELETE | `/api/v1/tags/batch` | 批量删除标签 |
| POST | `/api/v1/tags/merge` | 合并标签 |
| PATCH | `/api/v1/tags/batch/rename` | 批量重命名 |

### 复盘统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/review/weekly` | 本周统计数据 + 待办列表 |
| GET | `/api/v1/review/monthly` | 月度趋势数据（近30天录入趋势、标签分布） |
| GET | `/api/v1/review/stats` | 全局统计数据（总卡片、总行动项、完成率等） |

### 提醒系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/reminders/summary` | 提醒汇总（到期/逾期数量） |
| GET | `/api/v1/reminders/due-soon` | 即将到期行动项 |
| GET | `/api/v1/reminders/overdue` | 已逾期行动项 |

### 数据导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/export/digests` | 导出知识卡片（Markdown/JSON/CSV） |
| GET | `/api/v1/export/actions` | 导出行动项（CSV/JSON） |

### RSS 订阅

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/rss` | RSS 订阅列表 |
| POST | `/api/v1/rss` | 添加 RSS 订阅 |
| PUT | `/api/v1/rss/{id}` | 更新 RSS 订阅配置 |
| DELETE | `/api/v1/rss/{id}` | 删除 RSS 订阅 |
| POST | `/api/v1/rss/{id}/fetch` | 手动触发立即抓取 |

### Webhook

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/webhook/feishu` | 飞书机器人消息回调 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/auth/logout` | 退出登录（Token 失效） |

所有 API 需要 Header: `X-API-Key: <your-api-key>` 或 `Authorization: Bearer <jwt-token>`

## API 使用示例

### 提交信息（异步处理）

```bash
curl -X POST http://localhost:8001/api/v1/digest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-2026" \
  -d '{
    "source_type": "text",
    "content": "FastAPI 是一个现代、高性能的 Python Web 框架..."
  }'
```
返回 `task_id`，然后轮询获取结果：
```bash
curl http://localhost:8001/api/v1/digest/{task_id} \
  -H "X-API-Key: dev-api-key-2026"
```

### 查询知识卡片

```bash
curl "http://localhost:8001/api/v1/digest?page=1&page_size=20&keyword=Python" \
  -H "X-API-Key: dev-api-key-2026"
```

### 更新行动项

```bash
curl -X PATCH http://localhost:8001/api/v1/actions/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-2026" \
  -d '{"status": "done"}'
```

## Dify Workflow 配置

在 Dify 中创建 Workflow 类型应用：

**输入变量：**
- `input_text` (string): 待处理的正文内容
- `source_type` (string): 来源类型 (text/url)

**LLM 节点建议：**

节点 2 - 摘要生成:
```
你是一个专业的内容摘要助手。请为以下内容生成100字以内的核心摘要。
要求：提炼核心观点、语言精练、不使用套话开头
内容：{{input_text}}
```

节点 3 - 行动项提取:
```
你是一个行动项提取专家。请从以下内容中提取可执行的行动项。
要求：每个行动项必须以动词开头；具体可执行可验证；避免模糊表述；
      为每个行动项评估优先级：high/medium/low；提取1-10个行动项
内容：{{input_text}}
```

节点 4 - 标签生成:
```
你是一个标签分类专家。请为以下内容生成3-5个标签。
要求：覆盖技术领域/主题/场景；2-4字或英文单词；不用宽泛标签；不带#号
```

**输出格式（JSON 模式）：**
```json
{
  "summary": "100字以内核心摘要",
  "action_items": [
    {"content": "可执行行动项", "priority": "high|medium|low"}
  ],
  "tags": ["标签1", "标签2", "标签3"]
}
```

## 项目结构

```
Info-Butler/
├── backend/
│   ├── api/v1/            # API 路由层
│   │   ├── digest.py      #   信息录入 & 知识卡片
│   │   ├── actions.py     #   行动项 CRUD
│   │   ├── tags.py        #   标签管理
│   │   ├── review.py      #   复盘统计
│   │   ├── rss.py         #   RSS 订阅管理
│   │   └── webhook.py     #   飞书 Webhook 回调
│   ├── clients/           # 外部服务客户端
│   │   ├── dify_client.py #   Dify AI 调用（含重试）
│   │   ├── scraper_client.py  # URL 内容抓取
│   │   └── feishu_client.py   # 飞书 Webhook 通知
│   ├── core/              # 核心基础设施
│   │   ├── config.py      #   配置加载（.env）
│   │   ├── database.py    #   异步数据库引擎
│   │   ├── redis.py       #   Redis 连接
│   │   ├── security.py    #   API Key 鉴权
│   │   └── exceptions.py  #   全局异常定义
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── schemas/           # Pydantic 请求/响应模型
│   ├── services/          # 业务逻辑层
│   ├── workers/           # ARQ 异步任务
│   │   ├── tasks.py       #   digest 处理任务
│   │   ├── arq_client.py  #   ARQ 连接池
│   │   ├── worker_settings.py  # Worker 配置
│   │   └── run_worker.py  #   独立启动脚本
│   └── main.py            # FastAPI 入口
├── frontend/
│   ├── src/
│   │   ├── api/index.ts   # Axios 封装（错误拦截）
│   │   ├── router/        # Vue Router 路由
│   │   ├── views/         # 页面组件
│   │   │   ├── DigestNew.vue   # 信息录入
│   │   │   ├── DigestList.vue  # 知识卡片列表
│   │   │   ├── Actions.vue     # 行动项看板
│   │   │   ├── RSSManage.vue   # RSS 订阅管理
│   │   │   └── Review.vue      # 周报复盘
│   │   └── App.vue        # 根组件（Naive UI Provider）
│   └── vite.config.ts     # Vite 配置（代理 + 组件自动导入）
├── alembic/               # 数据库迁移
├── .env                   # 环境变量（不入库）
├── .gitignore
├── pyproject.toml         # Python 项目配置
├── tasks.md               # 开发任务跟踪
└── README.md
```

## 开发命令

```bash
# 后端
uv run ruff check backend/          # 代码检查
uv run pytest                       # 运行测试
uv run alembic revision --autogenerate -m "desc"  # 生成迁移
uv run alembic upgrade head         # 执行迁移

# 前端
cd frontend && npm run dev          # 开发服务器
cd frontend && npm run build        # 生产构建
cd frontend && npx vue-tsc --noEmit # 类型检查
```

## 当前开发进度

- [x] Phase 1: MVP 核心功能（14/14 完成）
- [x] Phase 2: 异步任务 + 错误处理（9/9 完成）
- [x] Phase 3: 完善 + 优化（8/8 完成）✅ 全部完成
- [x] Phase 4: 功能完善与优化（5/5 + 2 补充完成）✅ 全部完成
- [x] Phase 5: 数据洞察与生产力增强（10/10 完成）✅ 全部完成
  - ✅ 5.1 数据导出（Markdown/JSON/CSV）
  - ✅ 5.2 仪表盘可视化（ECharts 图表、30天趋势、标签分布）
  - ✅ 5.3 知识卡片批量管理（删除/归档/添加标签）
  - ✅ 5.4 行动项批量管理增强（删除/优先级/标签）
  - ✅ 5.5 标签批量管理（删除/合并/重命名）
  - ✅ 5.6 全文搜索增强（MySQL FULLTEXT + 关键词高亮）
  - ✅ 5.7 行动项提醒系统（到期/逾期视觉标记）
  - ✅ 5.8 信息详情页增强（关联推荐）
  - ✅ 5.9 单元测试与集成测试完善（24 个测试通过）
  - ✅ 5.10 API 限流与安全加固（密码校验/Token黑名单/CORS/安全头）
- [x] Phase 6: 多渠道输入 & 飞书双向集成（3/3 完成）✅ 全部完成
  - ✅ 6.1 文件上传解析（PDF/Word/Excel/TXT/Markdown）
  - ✅ 6.2 RSS 订阅自动抓取（订阅管理 + 自动解析）
  - ✅ 6.3 飞书双向集成（Webhook 回调 + 自动处理）

详细进度见 [tasks.md](./tasks.md)

## License

MIT
