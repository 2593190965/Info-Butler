# Info-Butler Phase 1 MVP 任务追踪

> 开始日期：2026-04-20 | 目标：跑通"输入 → AI 处理 → 落库"闭环

---

## 任务清单

### 1.1 uv 初始化项目 + 依赖安装
- [x] **已完成** 2026-04-20
- **完成情况：** 使用 `uv init` 初始化项目，安装全部生产依赖（fastapi, sqlalchemy, aiomysql, arq, httpx, readability-lxml, pydantic-settings 等）和开发依赖（pytest, ruff）
- **遇到问题：** 无

### 1.2 MySQL 建表 + Alembic 初始化
- [x] **已完成** 2026-04-20
- **完成情况：** ORM 模型定义完成后，FastAPI lifespan 中通过 `Base.metadata.create_all` 自动建表（MVP 阶段暂不使用 Alembic 迁移，Phase 2 引入）
- **DDL 位置：** dev-guide.md 第 3.3 节包含完整 DDL
- **注意：** 需要用户先启动 MySQL 并创建数据库（见 user-to-do-list.md 任务 #2）

### 1.3 FastAPI 应用骨架 + 配置加载
- [x] **已完成** 2026-04-20
- **完成情况：**
  - `backend/main.py`：FastAPI 应用入口，含 lifespan 自动建表 + /health 端点
  - `backend/core/config.py`：Pydantic BaseSettings 配置模型，支持 .env 文件
  - `backend/core/database.py`：async SQLAlchemy engine + sessionmaker
  - `backend/core/redis.py`：Redis 异步连接池
  - `backend/core/security.py`：API Key 鉴权中间件
  - `backend/core/base.py`：SQLAlchemy DeclarativeBase（解决循环导入）
- **遇到问题：** 初始版本存在循环导入（database ↔ models），已通过独立 base.py 解决

### 1.4 ORM 模型定义（RawInfo, ActionItem, Tag）
- [x] **已完成** 2026-04-20
- **完成情况：**
  - `backend/models/raw_info.py`：RawInfo 表（source_type, source_url, raw_text, summary, status, error_msg, dify_raw_response）+ tags 多对多关系
  - `backend/models/action_item.py`：ActionItem 表（info_id FK, content, status, priority, due_date）+ info relationship
  - `backend/models/tag.py`：Tag 表 + info_tags_table / action_tags_table 关联表
- **遇到问题：** 无

### 1.5 Pydantic Schema 定义
- [x] **已完成** 2026-04-20
- **完成情况：**
  - `backend/schemas/digest.py`：DigestCreate, DigestAccepted, DigestResponse, DigestListResponse, PaginatedDigests
  - `backend/schemas/action_item.py`：ActionItemCreate, ActionItemUpdate, ActionItemResponse, BatchActionUpdate, PaginatedActions
  - `backend/schemas/tag.py`：TagResponse
  - `backend/schemas/dify_response.py`：DifyResponse + ActionItemOutput（强校验 Schema）
- **遇到问题：** 无

### 1.6 Dify Workflow 搭建 + 测试
- [ ] **待开始** → 见 user-to-do-list.md（用户任务）
- **说明：** 需要在 Dify 平台搭建 Workflow，AI 无法替代

### 1.7 Dify Client 封装
- [x] **已完成** 2026-04-20
- **完成情况：** `backend/clients/dify_client.py`
  - DifyClient 类封装了 `/workflows/run` API 调用
  - 支持 workflow_id 参数传递
  - 包含 `validate_response()` 方法进行 Pydantic 强校验
  - 校验失败返回 None，由调用方处理异常队列逻辑
- **遇到问题：** 无（但需要用户配置 DIFY_API_KEY 才能实际运行）

### 1.8 Scraper Client 封装（URL 正文抓取）
- [x] **已完成** 2026-04-20
- **完成情况：** `backend/clients/scraper_client.py`
  - ScraperClient 类封装 httpx 异步 HTTP 请求
  - 优先使用 readability-lxml 提取正文（标题+纯文本）
  - readability 降级方案：HTMLParser 手动提取文本（过滤 script/style 标签）
  - 抓取失败抛出 ValueError，由上层捕获并标记 failed
- **遇到问题：** 无

### 1.9 POST /api/v1/digest（同步版本）
- [x] **已完成** 2026-04-20
- **完成情况：**
  - 接收 DigestCreate（source_type + content + title）
  - 写入 raw_infos（status=processing）
  - 同步调用 process_digest_sync：
    - URL 类型 → 先抓取正文
    - 调用 Dify Workflow → Pydantic 校验 → 写入 summary/action_items/tags
    - 失败 → 更新状态为 failed/parse_error
  - 返回 202 + task_id
- **遇到问题：** 无

### 1.10 GET /api/v1/digest/{task_id}
- [x] **已完成** 2026-04-20
- **完成情况：** 按 task_id 查询 raw_info，聚合返回摘要、标签列表、行动项详情

### 1.11 GET /api/v1/actions
- [x] **已完成** 2026-04-20
- **完成情况：** 支持按 status/priority 过滤、分页，关联显示 info_summary

### 1.12 PATCH /api/v1/actions/{id}
- [x] **已完成** 2026-04-20
- **完成情况：** 支持更新 status/priority/due_date；额外提供 PATCH /batch 批量操作

### 1.13 API Key 鉴权中间件
- [x] **已完成** 2026-04-20
- **完成情况：** `backend/core/security.py` 通过 X-API-Key Header 鉴权，所有 API 路由均已注入

### 1.14 端到端测试（HTTPie）
- [ ] **待开始**
- **说明：** 需要 MySQL + Redis + Dify 全部就绪后测试
- **前置条件：** user-to-do-list.md 中 #1 #2 #3 完成

---

## 额外完成项（超出 Phase 1 原始范围）

### E1. 路由冲突修复
- [x] **已完成**
- **问题：** `PATCH /api/v1/actions/batch` 原本定义在 `/{action_id}` 之后，导致 `batch` 被当作 `action_id` 参数
- **修复：** 将 batch 路由移至 `/{action_id}` 之前

### E2. 复盘统计接口（GET /api/v1/review/weekly）
- [x] **已完成**
- **新增文件：**
  - `backend/services/review_service.py`：周报统计逻辑（本周新增信息数、行动项数、完成率、待办列表）
  - `backend/api/v1/review.py`：复盘 API 端点
- **功能：** 按周聚合统计数据，支持自定义 week_start 参数

### E3. Alembic 迁移配置
- [x] **已完成**
- **新增文件：**
  - `alembic.ini`：迁移配置（已设置 MySQL DSN）
  - `alembic/env.py`：异步迁移环境（已导入所有 ORM 模型）
  - `alembic/versions/`：迁移脚本目录
- **使用方式：** MySQL 就绪后运行 `uv run alembic revision --autogenerate -m "init"` 生成初始迁移

---

## 进度总览

| 已完成 | 进行中 | 待开始 |
|--------|--------|--------|
| 15/17  | 0      | 2      |

## 当前阻塞项

| 阻塞原因 | 依赖的用户任务 | 说明 |
|---------|---------------|------|
| 无阻塞 | - | Phase 1-3 开发任务全部完成 |

## 完整路由清单（13 个 API）

```
POST   /api/v1/digest              提交信息（文本/URL）
GET    /api/v1/digest              知识卡片列表（分页+筛选）
GET    /api/v1/digest/{task_id}    查询处理结果详情
GET    /api/v1/actions             行动项列表（按状态/优先级筛选）
PATCH  /api/v1/actions/batch       批量更新行动项状态
PATCH  /api/v1/actions/{id}        更新单个行动项
GET    /api/v1/tags                标签列表
POST   /api/v1/tags                创建标签
PUT    /api/v1/tags/{id}           更新标签
DELETE /api/v1/tags/{id}           删除标签
GET    /api/v1/review/weekly       周复盘报告
GET    /health                     健康检查
```

## 已创建文件清单

```
Info-Butler/
├── pyproject.toml              ✅ uv 项目配置 + ruff 配置
├── .env.example                ✅ 环境变量模板
├── .env                        ✅ 开发环境配置
├── .gitignore                  ✅ Git 忽略规则
├── prd.md                      ✅ 产品需求文档
├── dev-guide.md                ✅ 开发文档
├── tasks.md                    ✅ 本文件 - 任务追踪
├── user-to-do-list.md          ✅ 用户待办清单
├── alembic/                     ✅ 数据库迁移
│   ├── ini                      ✅
│   ├── env.py                   ✅ 异步迁移环境
│   └── versions/                ✅ 迁移脚本目录
│
├── backend/
│   ├── __init__.py             ✅
│   ├── main.py                 ✅ FastAPI 入口 + lifespan
│   ├── core/
│   │   ├── __init__.py         ✅
│   │   ├── base.py             ✅ SQLAlchemy Base（解决循环导入）
│   │   ├── config.py           ✅ Settings (Pydantic)
│   │   ├── database.py         ✅ async engine + sessionmaker
│   │   ├── redis.py            ✅ Redis 连接池
│   │   └── security.py         ✅ API Key 鉴权
│   ├── models/
│   │   ├── __init__.py         ✅
│   │   ├── raw_info.py         ✅ RawInfo ORM
│   │   ├── action_item.py      ✅ ActionItem ORM
│   │   └── tag.py              ✅ Tag + 关联表
│   ├── schemas/
│   │   ├── __init__.py         ✅
│   │   ├── digest.py           ✅ Digest 相关 Schema
│   │   ├── action_item.py      ✅ ActionItem 相关 Schema
│   │   ├── tag.py              ✅ Tag Schema
│   │   └── dify_response.py    ✅ Dify 强校验 Schema
│   ├── clients/
│   │   ├── __init__.py         ✅
│   │   ├── dify_client.py      ✅ Dify API 封装
│   │   ├── scraper_client.py   ✅ URL 抓取封装
│   │   └── feishu_client.py    ✅ 飞书 Webhook 通知
│   ├── services/
│   │   ├── __init__.py         ✅
│   │   ├── digest_service.py   ✅ 信息处理核心业务逻辑
│   │   ├── action_service.py   ✅ 行动项 CRUD
│   │   ├── tag_service.py      ✅ 标签查询
│   │   └── review_service.py   ✅ 复盘统计（周报）
│   ├── api/
│   │   ├── __init__.py         ✅
│   │   ├── deps.py             ✅ 依赖注入
│   │   └── v1/
│   │       ├── __init__.py     ✅
│   │       ├── router.py       ✅ v1 路由聚合
│   │       ├── digest.py       ✅ /digest 路由
│   │       ├── actions.py      ✅ /actions 路由
│   │       ├── tags.py         ✅ /tags 路由
│   │       └── review.py       ✅ /review 路由
│   └── workers/
│       ├── __init__.py         ✅
│       └── tasks.py            ✅ ARQ Worker 定义（Phase 2 用）
│
└── tests/
    ├── __init__.py             ✅
    ├── conftest.py             ✅ pytest fixture
    ├── test_digest.py          ✅ digest 测试
    └── test_actions.py         ✅ actions 测试
```

---

# Phase 2：业务化改造

> 开始日期：2026-04-21 | 目标：异步化 + Vue3 前端 + 完整产品形态

---

## 任务清单

### 2.1 Redis 连接池 + ARQ 异步任务队列配置
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `backend/workers/worker_settings.py`：ARQ WorkerSettings（使用 settings.redis_db）
  - `backend/workers/arq_client.py`：ARQ 连接池管理 + enqueue_digest 入队函数
  - `backend/workers/tasks.py`：process_digest 任务函数（完善错误处理）
  - `backend/main.py`：lifespan 中管理 ARQ pool 生命周期
- **说明：** development 模式同步处理，production 模式走 ARQ 异步队列

### 2.2 POST digest 同步改异步（ARQ Worker）
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `backend/api/v1/digest.py`：根据 app_env 判断同步/异步
  - production → enqueue_digest 入队返回 202
  - development → process_digest_sync 同步处理
- **依赖：** 2.1 ✅

### 2.3 Dify 输出强校验 + 异常重试机制
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `backend/clients/dify_client.py`：
    - 3 次重试 + 指数退避 (2s, 4s)
    - `_normalize_output()` 容错处理（list→str, str→list）
    - `validate_response()` 自动补全 tags/action_items
- **遇到问题：** 无
- **依赖：** 2.2 ✅

### 2.4 全局异常处理 + 统一错误响应格式
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `backend/core/exceptions.py`：AppError / NotFoundError / ValidationError / ExternalServiceError
  - `backend/main.py`：app 级别 exception_handler（AppError + Exception兜底）
  - 统一返回 `{code, data, message}` 格式
- **注意：** APIRouter 不支持 exception_handler，需在 FastAPI app 层注册

### 2.5 Vue3 项目初始化 + 路由 + 基础布局
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `frontend/` 目录：Vue3 + Vite + TypeScript 项目
  - 技术栈：Vue3 + Pinia + Vue Router + Naive UI（暗色主题）
  - `frontend/src/App.vue`：侧边栏导航 + 主内容区布局
  - `frontend/src/router/index.ts`：4 个路由页面
  - `frontend/src/api/index.ts`：Axios 封装（自动注入 X-API-Key）
  - Vite proxy 配置：`/api` → `http://localhost:8001`
- **端口：** 前端 5173，后端 8001

### 2.6 信息录入页（文本/URL 提交）
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `frontend/src/views/DigestNew.vue`
  - 文本/URL 切换输入
  - 提交后自动轮询结果
  - 结果展示：摘要 + 标签 + 行动项列表

### 2.7 知识卡片列表页（分页+筛选）
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `frontend/src/views/DigestList.vue`
  - 卡片式列表展示
  - 关键词搜索 + 状态筛选
  - 分页加载

### 2.8 行动项看板页（状态看板+操作）
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `frontend/src/views/Actions.vue`
  - 三栏看板（待办 / 已完成 / 已忽略）
  - 优先级筛选
  - 单个操作按钮（完成/忽略/重开）

### 2.9 复盘仪表盘页（周报统计展示）
- [x] **已完成** 2026-04-21
- **完成情况：**
  - `frontend/src/views/Review.vue`
  - 本周概览卡片（新增信息、行动项、完成率）
  - 待办行动项列表（可直接完成）

---

## Phase 1 已完成项（回顾）

| # | 任务 | 状态 |
|---|------|------|
| 1.1 | uv 初始化项目 + 依赖安装 | ✅ |
| 1.2 | MySQL 建表 + Alembic 初始化 | ✅ |
| 1.3 | FastAPI 应用骨架 + 配置加载 | ✅ |
| 1.4 | ORM 模型定义 | ✅ |
| 1.5 | Pydantic Schema 定义 | ✅ |
| 1.6 | Dify Workflow 搭建 | ✅ (用户完成) |
| 1.7 | Dify Client 封装 | ✅ |
| 1.8 | Scraper Client 封装 | ✅ |
| 1.9 | POST /api/v1/digest | ✅ |
| 1.10 | GET /api/v1/digest/{task_id} | ✅ |
| 1.11 | GET /api/v1/actions | ✅ |
| 1.12 | PATCH /api/v1/actions/{id} | ✅ |
| 1.13 | API Key 鉴权中间件 | ✅ |
| 1.14 | 端到端测试 | ✅ |

## Phase 3 进度总览

| 已完成 | 进行中 | 待开始 |
|--------|--------|--------|
| 5      | 0      | 1      |

### 3.1 前后端联调 + 接口对齐
- [x] **已完成** 2026-04-21
- **修复项：**
  - Review 接口返回格式统一（移除 `{code, data, message}` 包裹）
  - Actions batch_update 返回格式统一
  - Review.vue 数据解析适配
- **验证结果：** Health / Review / Digest List / Actions 全部 ✅

### 3.2 URL 抓取功能（Scraper Client）
- [x] **已完成** 2026-04-21
- **说明：** ScraperClient 已完整实现（httpx + readability-lxml），已集成到 digest 流程
- **依赖：** httpx + readability-lxml（已在 pyproject.toml）

### 3.3 标签管理增强
- [x] **已完成** 2026-04-21
- **新增接口：**
  - GET /tags（列表 + 分页 + 搜索）
  - POST /tags（创建，去重）
  - PUT /tags/{id}（更新名称）
  - DELETE /tags/{id}（删除 + 清理关联）
- **增强：** 返回 info_count + action_count 统计

### 3.4 Dify Workflow 优化
- [x] **已完成** 2026-04-21
- **详细步骤：** 见 user-to-do-list.md → Phase 3 用户任务 → 第 8 节（Step 1-8）
- **包含：** Prompt 优化（3个节点）、输出模式配置、8种边界case测试、端到端验证、问题排查表、字符串JSON容错修复

### 3.5 生产环境配置
- [x] **已完成** 2026-04-21
- **新增文件：**
  - `backend/workers/run_worker.py`：ARQ Worker 独立启动脚本
  - `backend/workers/worker_settings.py`：增强配置（重试、超时、日志回调）
- **启动命令：** `uv run python -m backend.workers.run_worker`

### 3.6 前端细节打磨
- [x] **已完成** 2026-04-21
- **改进项：**
  - API 客户端错误处理增强（按状态码分类）
  - DigestNew 页面：URL 格式校验、轮询进度显示、超时处理、表单禁用
  - 错误提示友好化（statusLabel 中文映射）
  - 行动项看板状态切换
  - 复盘仪表盘数据展示
  - Naive UI 组件自动注册（unplugin-vue-components）
- **可能问题：** API 返回格式与前端期望不一致

### 3.7 飞书 Webhook 机器人通知
- [x] **已完成** 2026-04-21
- **新增文件：**
  - `backend/clients/feishu_client.py`：飞书 Webhook 客户端（文本消息 + 摘要通知）
- **修改文件：**
  - `backend/core/config.py`：新增 `feishu_webhook_url` 配置
  - `.env`：写入飞书 Webhook URL
  - `backend/services/digest_service.py`：处理完成/失败时自动发送飞书通知
- **功能：**
  - 处理成功 → 发送摘要+标签+行动项列表（带优先级图标）
  - 处理失败 → 发送警告消息
- **测试结果：** ✅ code=0, msg="success"

## Phase 3 进度总览

| 已完成 | 进行中 | 待开始 |
|--------|--------|--------|
| 8      | 0      | 0      |

### Phase 3 全部完成 ✅

---

# Phase 4：功能完善与优化

> 开始日期：2026-04-21 | 目标：补全缺失功能 + 提升用户体验

---

## 任务清单（规划中）

### 4.1 标签管理前端页面
- [x] **已完成** 2026-04-21
- **新增文件：** `frontend/src/views/Tags.vue`
- **功能：**
  - 标签列表（网格布局 + 分页）
  - 新建/编辑/删除标签（Modal 表单校验）
  - 关联统计（信息数 + 行动项数）
  - 关键词搜索
- **路由：** `/tags`

### 4.2 信息详情页优化
- [x] **已完成** 2026-04-21
- **新增文件：** `frontend/src/views/DigestDetail.vue`
- **功能：**
  - 完整摘要展示（原始内容可展开）
  - 标签列表（彩色圆角 Tag）
  - 行动项看板（完成/忽略/重开状态切换）
  - 优先级颜色标识
  - 来源 URL 外链跳转
  - 状态中文映射
- **路由：** `/digest/:task_id`
- **联动：**
  - DigestList 卡片点击 → 跳转详情
  - DigestNew 处理完成 → 「查看完整详情」链接

### 4.3 搜索功能增强
- [x] **已完成** 2026-04-21
- **修改文件：**
  - `frontend/src/router/index.ts`：新增 Detail + Tags 路由
  - `frontend/src/App.vue`：侧边栏添加「标签管理」入口
  - `frontend/src/views/DigestList.vue`：
    - 卡片点击跳转详情
    - 标签点击按名称筛选（@click.stop 阻止冒泡）
    - 状态显示中文化
    - filter-bar wrap 响应式

### 4.4 用户认证体系
- [x] **已完成** 2026-04-22
- **新增文件：**
  - `backend/models/user.py`：User ORM 模型（username/email/hashed_password/is_active）
  - `backend/schemas/auth.py`：注册/登录/Token/用户响应 Schema
  - `backend/api/v1/auth.py`：Auth 路由（register/login/me）
  - `frontend/src/views/Login.vue`：登录/注册页面
- **修改文件：**
  - `backend/core/security.py`：JWT Token 创建/验证 + 密码哈希 + 双模式鉴权（Bearer/API Key）
  - `backend/core/config.py`：新增 `jwt_secret` 配置
  - `backend/api/deps.py`：统一使用 `get_current_user`
  - `backend/api/v1/router.py`：注册 `/auth` 前缀路由
  - `frontend/src/api/index.ts`：JWT Bearer Token 拦截器 + 401 自动跳转登录
  - `frontend/src/router/index.ts`：Login 路由 + beforeEach 路由守卫
  - `frontend/src/App.vue`：侧边栏显示用户名 + 退出按钮
- **功能：**
  - 用户注册（用户名+邮箱+密码，bcrypt 哈希）
  - JWT 登录（7天有效期）
  - 当前用户信息查询 `/auth/me`
  - 兼容 API Key 模式（旧接口仍可用）
  - 路由守卫（未登录自动跳转 /login）
- **测试结果：** ✅ 注册 201 / 登录 200 返回 Token

### 4.5 定时任务 / 批量导入
- [x] **已完成** 2026-04-22
- **新增文件：**
  - `backend/schemas/batch.py`：批量导入/任务状态 Schema
  - `backend/api/v1/tasks.py`：Tasks 路由（batch/status）
- **API 接口：**
  - `POST /api/v1/tasks/batch` — 批量提交信息（最多20条，支持 text/url）
  - `GET /api/v1/tasks/status` — 队列监控（总数/待处理/完成/失败 + 最近10条）

## Phase 4 进度总览

| 已完成 | 进行中 | 待开始 |
|--------|--------|--------|
| 5      | 0      | 0      |

### Phase 4 全部完成 ✅

### 4.6 用户数据隔离（紧急修复）
- [x] **已完成** 2026-04-22
- **问题：** 所有用户共享同一份数据（知识卡片/标签/行动项/周报复盘）
- **修复方案：**
  - `RawInfo`、`Tag`、`ActionItem` 三张表新增 `user_id` 字段（FK → users.id）
  - `tags.name` 唯一约束改为 `(name, user_id)` 复合唯一索引
  - 所有 Service 层查询/写入强制带 `user_id` 过滤
  - 新增 `get_current_user_id` 依赖，从 JWT Token 提取用户 ID
  - API Key 模式默认使用 user_id=1
- **修改文件（共 12 个）：**
  - Models: `raw_info.py`, `tag.py`, `action_item.py`
  - Services: `digest_service.py`, `tag_service.py`, `action_service.py`, `review_service.py`
  - APIs: `digest.py`, `tags.py`, `actions.py`, `review.py`, `tasks.py`
  - Deps: `deps.py`
- **数据库迁移：** ALTER TABLE 添加 user_id 列 + 复合唯一索引
- **测试结果：** ✅ 双用户隔离测试通过（标签/digest/周报复盘均独立）

### 4.7 知识卡片筛选功能修复
- [x] **已完成** 2026-04-22
- **问题：**
  - 点击标签无法筛选列表
  - 状态下拉框缺少「待办」「已忽略」选项，且选择后不触发查询
- **修复：**
  - 前端 `DigestList.vue`：新增 `tagFilter` 状态，点击标签通过 `tags` 参数筛选，再次点击取消
  - 前端：状态下拉框增加「全部/待办/已忽略」选项，选择后自动查询 (`@update:value="onStatusChange"`)
  - 后端 `digest_service.py`：补全 `list_digests` 的 tags 过滤逻辑（JOIN info_tags + Tag 表）
- **修改文件：**
  - [DigestList.vue](frontend/src/views/DigestList.vue) — 标签点击筛选 + 状态下拉自动查询 + 高亮选中标签
  - [digest_service.py](backend/services/digest_service.py) — tags 子查询过滤
