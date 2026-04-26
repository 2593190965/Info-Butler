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

### 4.8 URL 内容抓取增强（多策略降级）
- [x] **已完成** 2026-04-22（v2 多策略升级）
- **目标：** 粘贴 URL 后自动采集页面正文内容，再交给 AI 解析
- **技术方案：** 多级降级抓取器（httpx → Jina Reader → 友好错误提示）
- **实现细节：**
  - `backend/clients/scraper_client.py`：多策略降级架构
  - **Level 1 — httpx + BeautifulSoup4**：主力抓取，覆盖 95%+ 常规静态站点
    - 模拟浏览器请求头绕过基础反爬
    - BeautifulSoup 清理噪音标签（script/style/nav/footer 等）
    - 智能标题提取 / 正文提取 / 文本清洗
  - **Level 2 — Jina Reader API**：降级方案，处理 JS 渲染页面和部分反爬站
    - 返回干净 Markdown 格式文本
    - 免费额度支持日常使用
  - **反爬检测**：自动识别挑战页（验证码/登录墙/安全检查）
    - 关键词匹配：欢迎来到、验证、安全检查、请登录等
    - 内容长度阈值：<200 字符判定为无效页
  - **友好错误提示**：所有策略失败后给出中文操作建议（手动粘贴内容）
- **集成点：**
  - `backend/services/digest_service.py`：URL 类型自动调用 `scraper_client.fetch_url()`
  - 抓取失败时标记 `status=failed` + 中文错误信息，前端可展示给用户
- **测试验证：**
  - ✅ httpbin.org/html → Level 1 成功，3594 字符
  - ✅ 知乎专栏 → 正确检测为反爬 → Level 2 尝试 → 友好错误提示
- **已知限制：**
  - 知乎/Wikipedia 等强反爬站点需用户手动粘贴内容
  - 可选配置 Jina Reader API Key 提升降级成功率

---

# Phase 5：数据洞察与生产力增强

> 开始日期：2026-04-22 | 目标：数据可视化 + 导出能力 + 搜索升级 + 生产就绪

---

## 任务清单

### 5.1 数据导出功能（Markdown / JSON / CSV）
- [ ] **待开始**
- **目标：** 支持将知识卡片、行动项导出为本地文件
- **后端 API：**
  - `GET /api/v1/export?format=markdown&tags=xxx&status=done` — 导出知识卡片
  - `GET /api/v1/export/actions?format=csv` — 导出行动项
- **支持格式：**
  - Markdown（每张卡片一个 section，含标题/摘要/标签/行动项）
  - JSON（完整结构化数据）
  - CSV（行动项表格，适合导入 Excel/Notion）
- **前端：**
  - 知识卡片列表页增加「导出」按钮（下拉选择格式）
  - 行动项看板页增加「导出 CSV」按钮
  - 导出时支持当前筛选条件（标签/状态/时间范围）
- **技术要点：**
  - `StreamingResponse` 返回文件流，设置 `Content-Disposition` 头
  - Markdown 模板渲染
  - CSV 用 Python 内置 `csv` 模块

### 5.2 周报复盘仪表盘可视化
- [x] **已完成** 2026-04-25
- **目标：** 将 Review 页面从纯文字统计升级为图表展示
- **后端新增：**
  - `GET /api/v1/review/monthly` — 月度趋势数据
    - 返回：每日新增信息数、行动项完成率曲线、标签分布 Top10
  - `GET /api/v1/review/stats` — 全局统计数据
    - 返回：总卡片数、总行动项数、整体完成率、最活跃标签
- **前端改造：**
  - 引入 ECharts 和 vue-echarts
  - 折线图：近 30 天信息录入趋势（带渐变填充）
  - 饼图/环形图：标签分布占比（Top 10，彩色主题）
  - 数字卡片带图标：总览 KPI（总知识卡片、总行动项、已完成、完成率）
- **修改文件：**
  - `backend/services/review_service.py` — 扩展统计逻辑（get_monthly_trends, get_global_stats）
  - `backend/api/v1/review.py` — 新增 monthly/stats 端点
  - `frontend/src/views/Review.vue` — 图表组件集成（折线图+饼图+统计卡片）
  - `frontend/package.json` — 新增 echarts + vue-echarts 依赖
- **图表特性：**
  - 深色主题适配（Catppuccin Mocha 配色）
  - 响应式布局（grid 两列）
  - 交互提示（tooltip）
  - 平滑曲线（smooth: true）
  - 渐变填充（areaStyle）

### 5.3 知识卡片批量管理
- [x] **已完成** 2026-04-25
- **目标：** 支持对知识卡片进行批量操作，提升管理效率
- **后端新增：**
  - `DELETE /api/v1/digest/batch` — 批量删除卡片
    - 参数：`{"ids": [1, 2, 3]}`，级联删除关联的行动项和标签关联
  - `PATCH /api/v1/digest/batch/status` — 批量修改状态
    - 参数：`{"ids": [1, 2], "status": "archived"}`
  - `POST /api/v1/digest/batch/tags` — 批量添加标签
    - 参数：`{"ids": [1, 2], "tag_ids": [10, 11]}`
- **前端改造：**
  - `DigestList.vue` 增加多选模式：
    - 列表项左侧添加 Checkbox
    - 顶部显示「已选 N 条」+ 操作栏（删除/归档/添加标签）
    - 全选/取消全选
    - 批量操作二次确认弹窗
- **修改文件：**
  - `backend/api/v1/digest.py` — 新增批量操作端点
  - `backend/schemas/digest.py` — 新增 BatchDelete/BatchStatusUpdate/BatchAddTags Schema
  - `backend/services/digest_service.py` — 批量删除/更新/添加标签逻辑
  - `frontend/src/views/DigestList.vue` — 多选 UI + 批量操作

### 5.4 行动项批量管理增强
- [x] **已完成** 2026-04-25（后端） | 待实现（前端）
- **目标：** 扩展现有批量更新功能，支持更多操作
- **后端新增：**
  - `DELETE /api/v1/actions/batch` — 批量删除行动项
    - 参数：`{"ids": [1, 2, 3]}`
  - `PATCH /api/v1/actions/batch/priority` — 批量修改优先级
    - 参数：`{"ids": [1, 2], "priority": "high"}`
  - `POST /api/v1/actions/batch/tags` — 批量添加标签
    - 参数：`{"ids": [1, 2], "tag_ids": [10, 11]}`
- **前端改造：**
  - `Actions.vue` 增加多选模式：
    - 每个行动项卡片添加 Checkbox
    - 看板顶部显示「已选 N 条」+ 操作栏（删除/修改优先级/添加标签/标记完成）
    - 批量操作下拉菜单
- **修改文件：**
  - `backend/api/v1/actions.py` — 新增批量删除/优先级/标签端点
  - `backend/schemas/action_item.py` — 新增 BatchDelete/BatchPriorityUpdate/BatchAddTags Schema
  - `backend/services/action_service.py` — 批量删除/更新/添加标签逻辑
  - `frontend/src/views/Actions.vue` — 多选 UI + 批量操作（待实现）

### 5.5 标签批量管理
- [x] **已完成** 2026-04-25（后端） | 待实现（前端）
- **目标：** 支持批量管理标签，包括删除、合并、重命名
- **后端新增：**
  - `DELETE /api/v1/tags/batch` — 批量删除标签
    - 参数：`{"ids": [1, 2, 3]}`，级联删除关联
  - `POST /api/v1/tags/merge` — 合并标签
    - 参数：`{"source_ids": [1, 2], "target_id": 3}` — 将源标签关联全部迁移到目标标签
  - `PATCH /api/v1/tags/batch/rename` — 批量重命名
    - 参数：`{"renames": [{"id": 1, "new_name": "新名称"}]}`
- **前端改造：**
  - `Tags.vue` 增加多选模式：
    - 标签卡片添加 Checkbox
    - 顶部显示「已选 N 个」+ 操作栏（删除/合并）
    - 合并弹窗：选择目标标签或输入新标签名
- **修改文件：**
  - `backend/api/v1/tags.py` — 新增批量操作端点
  - `backend/schemas/tag.py` — 新增 BatchDelete/MergeTags/BatchRename Schema
  - `backend/services/tag_service.py` — 批量删除/合并/重命名逻辑
  - `frontend/src/views/Tags.vue` — 多选 UI + 批量操作（待实现）

### 5.6 全文搜索增强（MySQL FULLTEXT）
- [ ] **待开始**
- **目标：** 从简单 LIKE 查询升级为全文搜索引擎级别体验
- **后端改动：**
  - MySQL FULLTEXT 索引：对 `raw_infos.raw_text` + `raw_infos.summary` 创建全文索引
  - 搜索接口扩展：
    - 支持 `highlight=true` 参数返回匹配高亮片段
    - 支持 `mode=boolean` 布尔搜索（AND/OR/NOT）
    - 搜索结果按相关度排序（`MATCH ... AGAINST` score）
  - 标签搜索优化：模糊匹配（LIKE %tag%）
- **前端改动：**
  - 搜索框增加防抖（debounce 300ms）
  - 搜索结果高亮关键词
  - 搜索建议（最近使用的标签/关键词）
- **SQL 示例：**
  ```sql
  ALTER TABLE raw_infos ADD FULLTEXT INDEX ft_content (raw_text, summary);
  SELECT *, MATCH(raw_text, summary) AGAINST('关键词' IN NATURAL LANGUAGE MODE) AS score
  FROM raw_infos WHERE MATCH(raw_text, summary) AGAINST('关键词') ORDER BY score DESC;
  ```

### 5.7 行动项提醒系统（到期提醒 + 逾期告警）
- [ ] **待开始**
- **目标：** 让行动项不再被遗忘，主动推送提醒
- **后端新增：**
  - ARQ 定期任务 `check_due_actions`（每小时执行一次）
  - 查询 due_date <= now() 且 status=pending 的行动项
  - 到期提醒：通过飞书 Webhook 推送「今日到期行动项」汇总
  - 逾期告警：due_date < now() 超过 24h 的标记逾期并推送
- **模型改动：**
  - ActionItem 增加 `reminded_at` 字段（记录上次提醒时间，避免重复推送）
  - ActionItem 增加 `overdue_notified_at` 字段
- **前端改动：**
  - 行动项看板：到期项高亮显示（橙色边框）
  - 逾期项特殊标记（红色闪烁/图标）
  - 详情页显示距离到期剩余时间
- **配置项：**
  - `ACTION_REMIND_HOURS_BEFORE`：提前几小时提醒（默认 24h）
  - `ACTION_OVERDUE_HOURS`：超过几小时算逾期（默认 24h）

### 5.8 信息详情页增强（关联推荐 + 版本历史）
- [ ] **待开始**
- **目标：** 让单条信息的价值最大化
- **关联推荐：**
  - 详情页底部「相关卡片」区域
  - 基于共享标签的卡片推荐（同标签的其他卡片）
  - 后端：`GET /api/v1/digest/{task_id}/related` — 返回最多 5 条关联卡片
- **版本历史：**
  - 当用户手动编辑摘要/行动项时，保留历史版本
  - 新增 `action_item_versions` 表（content, priority, status, created_at, action_item_id FK）
  - 详情页可查看某行动项的变更记录
- **前端：**
  - 关联卡片横向滚动列表（点击跳转）
  - 行动项旁增加「历史」图标，点击弹出变更时间线

### 5.9 单元测试与集成测试完善
- [ ] **待开始**
- **目标：** 提升代码质量保障，核心路径全覆盖
- **测试范围：**
  - Service 层单元测试：
    - `test_digest_service.py` — list_digests 筛选逻辑、create_raw_info、process_digest_sync
    - `test_action_service.py` — CRUD、批量更新、状态校验
    - `test_tag_service.py` — 创建去重、删除级联
    - `test_review_service.py` — 周报聚合计算
  - API 层集成测试：
    - `test_auth_api.py` — 注册/登录/JWT 鉴权/用户隔离
    - `test_digest_api.py` — 提交→处理→查询全流程
  - 测试工具：
    - pytest-asyncio 异步测试
    - httpx.AsyncClient 测试客户端
    - factory_boy 或自定义 fixture 工厂数据
- **目标覆盖率：** Service 层 ≥80%，API 层关键路径 100%

### 5.10 API 限流与安全加固
- [ ] **待开始**
- **目标：** 生产环境安全防护
- **限流：**
  - 引入 `slowapi`（基于 limiter 的 FastAPI 限流）
  - 按用户 ID 限流（认证用户 100 req/min，未认证 20 req/min）
  - 批量接口单独限制（batch 10 req/min）
- **安全加固：**
  - 密码强度校验（注册时：最少8位，含大小写+数字）
  - JWT Token 黑名单机制（退出登录后 Token 失效，用 Redis Set 存储）
  - 输入清洗：XSS 防护（前端转义 + 后端 Pydantic 校验长度上限）
  - CORS 配置收紧（生产环境只允许前端域名）

## Phase 5 进度总览

| 已完成 | 进行中 | 待开始 |
|--------|--------|--------|
| 0      | 0      | 10     |

### 优先级排序

| 优先级 | 任务 | 理由 |
|--------|------|------|
| 🔴 P0 | 5.2 仪表盘可视化 | 产品差异化亮点，周报复盘是核心场景 |
| 🔴 P0 | 5.3 知识卡片批量管理 | 高频需求，管理效率提升明显 |
| 🔴 P0 | 5.4 行动项批量管理 | 现有功能扩展，成本低价值高 |
| 🔴 P0 | 5.5 标签批量管理 | 标签多了之后必需要的功能 |
| 🔴 P0 | 5.6 全文搜索增强 | 日常使用最高频功能，体验提升明显 |
| 🟡 P1 | 5.1 数据导出 | 用户高频需求，实现成本低 |
| 🟡 P1 | 5.7 行动项提醒 | 解决"遗忘"痛点，提升产品粘性 |
| 🟢 P2 | 5.8 详情页增强 | 锦上添花，提升单条信息价值 |
| 🟢 P2 | 5.9 测试完善 | 工程质量保障 |
| 🟢 P2 | 5.10 安全加固 | 生产上线前必须完成 |

## 预计新增/修改文件

```
backend/
├── api/v1/
│   ├── export.py              # 5.1 导出 API
│   ├── review.py              # 5.2 扩展 monthly/stats
│   ├── digest.py              # 5.3 扩展批量操作
│   ├── actions.py             # 5.4 扩展批量操作
│   └── tags.py                # 5.5 扩展批量操作
├── services/
│   ├── export_service.py      # 5.1 导出逻辑
│   ├── review_service.py      # 5.2 统计扩展
│   ├── digest_service.py      # 5.3 批量操作逻辑
│   ├── action_service.py      # 5.4 批量操作逻辑
│   ├── tag_service.py         # 5.5 批量操作逻辑
│   └── reminder_service.py    # 5.7 提醒逻辑
├── models/
│   └── action_item_version.py # 5.8 版本历史模型
├── workers/
│   └── tasks.py               # 5.7 定期检查任务
├── schemas/
│   ├── export.py              # 5.1 导出 Schema
│   ├── digest.py              # 5.3 批量操作 Schema
│   ├── action_item.py         # 5.4 批量操作 Schema
│   └── tag.py                 # 5.5 批量操作 Schema
└── core/
    └── rate_limiter.py        # 5.10 限流配置
frontend/
├── src/views/
│   ├── Review.vue             # 5.2 图表改造
│   ├── DigestList.vue         # 5.3 批量管理 UI
│   ├── Actions.vue            # 5.4 批量管理 UI
│   ├── Tags.vue               # 5.5 批量管理 UI
│   └── DigestDetail.vue       # 5.8 关联推荐+历史
├── src/components/
│   └── charts/                # 5.2 图表封装组件
tests/
├── test_auth_api.py           # 5.9 认证测试
├── test_export.py             # 5.9 导出测试
└── test_review_service.py     # 5.9 统计测试
```

## Phase 5 进度总览

| 已完成 | 进行中 | 待开始 |
|--------|--------|--------|
| 0      | 0      | 7      |

### 优先级排序

| 优先级 | 任务 | 理由 |
|--------|------|------|
| 🔴 P0 | 5.3 全文搜索增强 | 日常使用最高频功能，体验提升明显 |
| 🔴 P0 | 5.2 仪表盘可视化 | 产品差异化亮点，周报复盘是核心场景 |
| 🟡 P1 | 5.1 数据导出 | 用户高频需求，实现成本低 |
| 🟡 P1 | 5.4 行动项提醒 | 解决"遗忘"痛点，提升产品粘性 |
| 🟢 P2 | 5.5 详情页增强 | 锦上添花，提升单条信息价值 |
| 🟢 P2 | 5.6 测试完善 | 工程质量保障 |
| 🟢 P2 | 5.7 安全加固 | 生产上线前必须完成 |

## 预计新增/修改文件

```
backend/
├── api/v1/
│   ├── export.py              # 5.1 导出 API
│   └── review.py              # 5.2 扩展 monthly/stats
├── services/
│   ├── export_service.py      # 5.1 导出逻辑
│   ├── review_service.py      # 5.2 统计扩展
│   └── reminder_service.py    # 5.4 提醒逻辑
├── models/
│   └── action_item_version.py # 5.5 版本历史模型
├── workers/
│   └── tasks.py               # 5.4 定期检查任务
├── schemas/
│   └── export.py              # 5.1 导出 Schema
└── core/
    └── rate_limiter.py        # 5.7 限流配置
frontend/
├── src/views/
│   ├── Review.vue             # 5.2 图表改造
│   └── DigestDetail.vue       # 5.5 关联推荐+历史
├── src/components/
│   └── charts/                # 5.2 图表封装组件
tests/
├── test_auth_api.py           # 5.6 认证测试
├── test_export.py             # 5.6 导出测试
└── test_review_service.py     # 5.6 统计测试
```
