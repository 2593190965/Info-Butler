# Info-Butler 开发文档

> 版本：v1.0 | 更新日期：2026-04-20 | 技术栈：uv + Python + MySQL + Vue3 + Redis + FastAPI

---

## 一、技术架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     Vue3 前端 (Vite)                     │
│          Element Plus + Pinia + Vue Router               │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / HTTPS
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI 网关层                           │
│          JWT 鉴权 · Pydantic 校验 · 异步路由              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌───────────┐             │
│  │ 信息输入  │  │ 行动项管理│  │ 检索与复盘 │             │
│  │ Service  │  │ Service  │  │  Service  │             │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘             │
│       │              │              │                    │
│  ┌────▼──────────────▼──────────────▼─────┐             │
│  │          SQLAlchemy (ORM)              │             │
│  └────┬──────────────┬──────────────┬─────┘             │
└───────┼──────────────┼──────────────┼───────────────────┘
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
   │  MySQL  │   │   Redis   │  │  Dify   │
   │ 业务数据 │   │ 缓存/队列 │  │ AI 引擎 │
   └─────────┘   └───────────┘  └─────────┘
                                      │
                                 ┌────▼────┐
                                 │  LLM    │
                                 │(GPT/等) │
                                 └─────────┘
```

### 1.2 技术栈明细

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 包管理 | uv | latest | Python 依赖管理与虚拟环境 |
| 后端框架 | FastAPI | 0.115+ | 异步 Web 框架 |
| ORM | SQLAlchemy | 2.0+ | 异步 ORM |
| 数据库 | MySQL | 8.0+ | 业务数据持久化 |
| 缓存/队列 | Redis | 7.0+ | 任务队列、缓存、会话 |
| 任务队列 | ARQ | 0.26+ | 基于 Redis 的异步任务队列 |
| AI 引擎 | Dify | Cloud/Self-hosted | Workflow 编排与 LLM 调用 |
| 数据校验 | Pydantic | 2.0+ | 请求/响应模型与强校验 |
| 前端框架 | Vue3 | 3.4+ | SPA 前端 |
| UI 组件库 | Element Plus | 2.7+ | 前端组件 |
| 状态管理 | Pinia | 2.1+ | 前端状态管理 |
| 构建工具 | Vite | 5.0+ | 前端构建 |
| HTTP 客户端 | httpx | 0.27+ | 异步 HTTP 请求（网页抓取、Dify API） |
| 网页解析 | readability-lxml | 0.8+ | URL 正文提取 |
| 向量检索 | LangChain + FAISS | Phase 2 | 语义检索 |

### 1.3 架构决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 任务队列选型 | ARQ（非 Celery） | 轻量、原生 async、Redis 依赖即可，无需额外 Broker |
| ORM 选型 | SQLAlchemy 2.0 async | 社区成熟、类型提示友好、支持异步 |
| 前端选型 | Vue3 + Element Plus | 生态成熟、组件丰富、适合后台管理类应用 |
| AI 引擎 | Dify | 低代码 Workflow 编排、Prompt 版本管理、可替换 |
| 包管理 | uv | 极速依赖解析、兼容 pyproject.toml |

---

## 二、项目结构

```
Info-Butler/
├── pyproject.toml                  # uv 项目配置 + 依赖声明
├── .python-version                 # Python 版本锁定
├── .env.example                    # 环境变量模板
├── alembic.ini                     # 数据库迁移配置
├── alembic/
│   └── versions/                   # 迁移脚本
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Settings（Pydantic BaseSettings）
│   │   ├── database.py             # SQLAlchemy async engine/session
│   │   ├── redis.py                # Redis 连接池
│   │   └── security.py             # API Key 鉴权
│   ├── models/
│   │   ├── __init__.py
│   │   ├── raw_info.py             # RawInfo ORM 模型
│   │   ├── action_item.py          # ActionItem ORM 模型
│   │   └── tag.py                  # Tag + 关联表 ORM 模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── digest.py               # 信息输入/输出 Schema
│   │   ├── action_item.py          # 行动项 Schema
│   │   ├── tag.py                  # 标签 Schema
│   │   └── dify_response.py        # Dify 返回值强校验 Schema
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # v1 路由聚合
│   │   │   ├── digest.py           # /api/v1/digest 相关
│   │   │   ├── actions.py          # /api/v1/actions 相关
│   │   │   └── tags.py             # /api/v1/tags 相关
│   │   └── deps.py                 # 依赖注入（DB session、鉴权等）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── digest_service.py       # 信息处理业务逻辑
│   │   ├── action_service.py       # 行动项业务逻辑
│   │   ├── tag_service.py          # 标签业务逻辑
│   │   └── review_service.py       # 复盘统计业务逻辑
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── tasks.py                # ARQ 任务定义
│   │   └── worker.py               # ARQ Worker 启动入口
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── dify_client.py          # Dify API 封装
│   │   └── scraper_client.py       # URL 正文抓取封装
│   └── utils/
│       ├── __init__.py
│       └── text.py                  # 文本处理工具
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   ├── digest.ts
│   │   │   ├── action.ts
│   │   │   └── tag.ts
│   │   ├── api/
│   │   │   ├── request.ts           # axios 封装
│   │   │   ├── digest.ts
│   │   │   ├── action.ts
│   │   │   └── tag.ts
│   │   ├── views/
│   │   │   ├── DigestInput.vue      # 信息录入页
│   │   │   ├── CardList.vue         # 知识卡片列表
│   │   │   ├── ActionBoard.vue      # 行动项看板
│   │   │   ├── ReviewDashboard.vue  # 复盘仪表盘
│   │   │   └── CardDetail.vue       # 卡片详情
│   │   ├── components/
│   │   │   ├── DigestForm.vue
│   │   │   ├── CardItem.vue
│   │   │   ├── ActionItem.vue
│   │   │   └── TagFilter.vue
│   │   └── styles/
│   │       └── global.css
│   └── index.html
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_digest.py
    ├── test_actions.py
    └── test_tags.py
```

---

## 三、数据库设计

### 3.1 ER 关系图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  raw_infos   │       │ action_items │       │    tags      │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │──1:N──│ id (PK)      │       │ id (PK)      │
│ source_type  │       │ info_id (FK) │       │ name (UQ)    │
│ source_url   │       │ content      │       │ created_at   │
│ raw_text     │       │ status       │       └──────┬───────┘
│ title        │       │ priority     │              │
│ summary      │       │ due_date     │              │
│ status       │       │ created_at   │              │
│ error_msg    │       │ updated_at   │              │
│ dify_raw_resp│       └──────┬───────┘              │
│ created_at   │              │                      │
│ updated_at   │              │                      │
└──────┬───────┘              │                      │
       │                      │                      │
       │    ┌─────────────────┴──────────────────────┘
       │    │
       │    │  M:N 关联表
       │    │
       │  ┌─┴──────────────┐   ┌──────────────────┐
       │  │  info_tags     │   │  action_tags     │
       │  ├────────────────┤   ├──────────────────┤
       │  │ info_id (FK)   │   │ action_id (FK)   │
       └──│ tag_id (FK)    │   │ tag_id (FK)      │
          └────────────────┘   └──────────────────┘
```

### 3.2 表结构详细定义

#### raw_infos（原始信息表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 主键 |
| source_type | VARCHAR(20) | NOT NULL, DEFAULT 'text' | 来源类型：text / url / voice |
| source_url | VARCHAR(2048) | NULL | 原始链接（URL 类型时填写） |
| title | VARCHAR(500) | NULL | 标题（从网页提取或用户输入） |
| raw_text | TEXT | NOT NULL | 原始正文内容 |
| summary | VARCHAR(200) | NULL | AI 生成的摘要（≤100字，预留余量） |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'processing' | 处理状态：processing / done / failed / parse_error |
| error_msg | VARCHAR(1000) | NULL | 错误原因（失败时记录） |
| dify_raw_response | JSON | NULL | Dify 原始返回（用于排查） |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：**
- `idx_status` ON (status)
- `idx_source_url` ON (source_url(255))
- `idx_created_at` ON (created_at)

#### action_items（行动项表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 主键 |
| info_id | BIGINT UNSIGNED | FK → raw_infos.id, NOT NULL | 关联原始信息 |
| content | VARCHAR(500) | NOT NULL | 行动项内容 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 状态：pending / done / ignored |
| priority | VARCHAR(10) | DEFAULT 'medium' | 优先级：high / medium / low |
| due_date | DATE | NULL | 截止日期 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：**
- `idx_info_id` ON (info_id)
- `idx_status` ON (status)
- `idx_due_date` ON (due_date)

#### tags（标签表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 主键 |
| name | VARCHAR(50) | NOT NULL, UNIQUE | 标签名（如 FastAPI） |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### info_tags（信息-标签关联表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| info_id | BIGINT UNSIGNED | FK → raw_infos.id, NOT NULL | 信息 ID |
| tag_id | BIGINT UNSIGNED | FK → tags.id, NOT NULL | 标签 ID |

**索引：**
- `pk_info_tags` PRIMARY KEY (info_id, tag_id)
- `idx_tag_id` ON (tag_id)

#### action_tags（行动项-标签关联表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| action_id | BIGINT UNSIGNED | FK → action_items.id, NOT NULL | 行动项 ID |
| tag_id | BIGINT UNSIGNED | FK → tags.id, NOT NULL | 标签 ID |

**索引：**
- `pk_action_tags` PRIMARY KEY (action_id, tag_id)
- `idx_tag_id` ON (tag_id)

### 3.3 DDL（参考）

```sql
CREATE DATABASE IF NOT EXISTS info_butler
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE info_butler;

CREATE TABLE raw_infos (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_type VARCHAR(20)  NOT NULL DEFAULT 'text',
    source_url  VARCHAR(2048) NULL,
    title       VARCHAR(500) NULL,
    raw_text    TEXT          NOT NULL,
    summary     VARCHAR(200) NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'processing',
    error_msg   VARCHAR(1000) NULL,
    dify_raw_response JSON NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_source_url (source_url(255)),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

CREATE TABLE action_items (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    info_id     BIGINT UNSIGNED NOT NULL,
    content     VARCHAR(500) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending',
    priority    VARCHAR(10)  DEFAULT 'medium',
    due_date    DATE NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_info_id (info_id),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date),
    CONSTRAINT fk_action_info FOREIGN KEY (info_id) REFERENCES raw_infos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE tags (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE info_tags (
    info_id BIGINT UNSIGNED NOT NULL,
    tag_id  BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (info_id, tag_id),
    INDEX idx_tag_id (tag_id),
    CONSTRAINT fk_it_info FOREIGN KEY (info_id) REFERENCES raw_infos(id) ON DELETE CASCADE,
    CONSTRAINT fk_it_tag  FOREIGN KEY (tag_id)  REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE action_tags (
    action_id BIGINT UNSIGNED NOT NULL,
    tag_id    BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (action_id, tag_id),
    INDEX idx_tag_id (tag_id),
    CONSTRAINT fk_at_action FOREIGN KEY (action_id) REFERENCES action_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_at_tag    FOREIGN KEY (tag_id)    REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB;
```

---

## 四、API 设计

### 4.1 通用约定

| 项目 | 规范 |
|------|------|
| 基础路径 | `/api/v1` |
| 鉴权方式 | `X-API-Key` Header |
| 响应格式 | `{"code": 0, "data": {...}, "message": "ok"}` |
| 错误响应 | `{"code": <非0>, "data": null, "message": "错误描述"}` |
| 分页参数 | `?page=1&page_size=20` |
| 时间格式 | ISO 8601（`2026-04-20T10:30:00Z`） |

### 4.2 接口列表

#### 4.2.1 信息输入

**POST /api/v1/digest**

提交信息，异步处理。

请求体：
```json
{
    "source_type": "url",
    "content": "https://example.com/article",
    "title": "可选标题"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_type | string | 是 | text / url |
| content | string | 是 | 纯文本内容或 URL |
| title | string | 否 | 标题（URL 类型时可选，系统自动提取） |

成功响应（202 Accepted）：
```json
{
    "code": 0,
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "processing"
    },
    "message": "ok"
}
```

#### 4.2.2 查询处理结果

**GET /api/v1/digest/{task_id}**

查询信息处理状态与结果。

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "id": 1,
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "source_type": "url",
        "source_url": "https://example.com/article",
        "title": "文章标题",
        "summary": "本文介绍了 FastAPI 的异步编程模式...",
        "status": "done",
        "tags": ["FastAPI", "异步编程", "Python"],
        "action_items": [
            {"id": 1, "content": "尝试在项目中使用 async/await 替换同步路由", "status": "pending"},
            {"id": 2, "content": "阅读 FastAPI 官方异步文档", "status": "pending"}
        ],
        "created_at": "2026-04-20T10:30:00Z"
    },
    "message": "ok"
}
```

#### 4.2.3 知识卡片列表

**GET /api/v1/digest**

查询知识卡片列表，支持筛选与分页。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 20 |
| tag | string | 否 | 标签过滤（多个用逗号分隔） |
| keyword | string | 否 | 关键词搜索（摘要 + 原文） |
| status | string | 否 | 处理状态过滤 |

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "items": [
            {
                "id": 1,
                "title": "文章标题",
                "summary": "摘要内容...",
                "tags": ["FastAPI", "异步编程"],
                "action_count": 2,
                "pending_action_count": 1,
                "created_at": "2026-04-20T10:30:00Z"
            }
        ],
        "total": 42,
        "page": 1,
        "page_size": 20
    },
    "message": "ok"
}
```

#### 4.2.4 行动项列表

**GET /api/v1/actions**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | pending / done / ignored |
| priority | string | 否 | high / medium / low |
| tag | string | 否 | 标签过滤 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "items": [
            {
                "id": 1,
                "content": "尝试在项目中使用 async/await",
                "status": "pending",
                "priority": "high",
                "due_date": "2026-04-25",
                "tags": ["FastAPI"],
                "info_summary": "本文介绍了 FastAPI 的异步编程模式...",
                "created_at": "2026-04-20T10:30:00Z"
            }
        ],
        "total": 15,
        "page": 1,
        "page_size": 20
    },
    "message": "ok"
}
```

#### 4.2.5 更新行动项

**PATCH /api/v1/actions/{id}**

请求体：
```json
{
    "status": "done",
    "priority": "high",
    "due_date": "2026-04-25"
}
```

所有字段均可选，只传需要更新的字段。

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "id": 1,
        "content": "尝试在项目中使用 async/await",
        "status": "done",
        "priority": "high",
        "due_date": "2026-04-25",
        "updated_at": "2026-04-21T08:00:00Z"
    },
    "message": "ok"
}
```

#### 4.2.6 批量更新行动项

**PATCH /api/v1/actions/batch**

请求体：
```json
{
    "ids": [1, 2, 3],
    "status": "done"
}
```

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "updated_count": 3
    },
    "message": "ok"
}
```

#### 4.2.7 标签列表

**GET /api/v1/tags**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 标签名模糊搜索 |

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "items": [
            {"id": 1, "name": "FastAPI", "info_count": 12, "action_count": 8},
            {"id": 2, "name": "异步编程", "info_count": 7, "action_count": 5}
        ]
    },
    "message": "ok"
}
```

#### 4.2.8 周复盘报告

**GET /api/v1/review/weekly**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| week_start | string | 否 | 周起始日期（默认本周一），格式 YYYY-MM-DD |

成功响应（200 OK）：
```json
{
    "code": 0,
    "data": {
        "week_start": "2026-04-14",
        "week_end": "2026-04-20",
        "new_info_count": 8,
        "new_action_count": 12,
        "done_action_count": 5,
        "ignored_action_count": 2,
        "completion_rate": 0.42,
        "top_tags": [
            {"name": "FastAPI", "count": 4},
            {"name": "架构设计", "count": 3}
        ],
        "pending_actions": [
            {"id": 3, "content": "阅读 FastAPI 中间件文档", "priority": "medium"}
        ]
    },
    "message": "ok"
}
```

---

## 五、Dify Workflow 设计

### 5.1 Workflow 节点定义

```
[Start] → [变量接收: text, source_type] → [LLM: 摘要] → [LLM: 行动项] → [LLM: 标签] → [End: JSON 输出]
```

### 5.2 输入变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| text | string | 正文内容 |
| source_type | string | 来源类型 |

### 5.3 输出 JSON Schema

```json
{
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "100字以内核心摘要",
            "maxLength": 100
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "可执行的行动项，以动词开头"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "优先级"
                    }
                },
                "required": ["content", "priority"]
            },
            "minItems": 1,
            "maxItems": 10
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 3,
            "maxItems": 5
        }
    },
    "required": ["summary", "action_items", "tags"]
}
```

### 5.4 Prompt 参考

**摘要节点 Prompt：**

```
你是一个专业的内容摘要助手。请为以下内容生成一段100字以内的核心摘要。

要求：
1. 提炼核心观点，不遗漏关键信息
2. 语言精练，避免冗余
3. 不使用"本文介绍了"等套话开头

内容：
{{text}}
```

**行动项节点 Prompt：**

```
你是一个行动项提取专家。请从以下内容中提取可执行的行动项。

要求：
1. 每个行动项必须以动词开头（如"学习"、"实现"、"阅读"、"配置"等）
2. 行动项必须具体、可执行、可验证完成
3. 避免模糊表述（如"了解"改为"阅读XX文档"）
4. 为每个行动项评估优先级：high（紧急重要）、medium（重要不紧急）、low（可延后）
5. 提取1-10个行动项

内容：
{{text}}

摘要：
{{summary}}
```

**标签节点 Prompt：**

```
你是一个标签分类专家。请为以下内容生成3-5个标签。

要求：
1. 标签应覆盖内容的技术领域、主题、应用场景
2. 标签用2-4个字或英文单词表示（如"FastAPI"、"架构设计"、"求职面经"）
3. 不要使用过于宽泛的标签（如"技术"、"编程"）
4. 标签不要带#号

内容摘要：
{{summary}}

行动项：
{{action_items}}
```

---

## 六、Redis 使用设计

### 6.1 用途规划

| 用途 | Key 格式 | TTL | 说明 |
|------|---------|-----|------|
| 任务状态缓存 | `task:{task_id}` | 1h | 存储异步任务处理状态，减少 DB 查询 |
| API 限流 | `ratelimit:{api_key}:{endpoint}` | 60s | 滑动窗口限流 |
| 标签缓存 | `tags:all` | 10min | 热门标签列表缓存 |
| 任务队列 | `arq:queue` | - | ARQ 任务队列 |

### 6.2 任务状态缓存结构

```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "done",
    "info_id": 1,
    "created_at": "2026-04-20T10:30:00Z"
}
```

---

## 七、异步任务设计

### 7.1 任务流程

```
FastAPI 接收请求
    │
    ├── 生成 task_id (UUID4)
    ├── 写入 raw_infos (status=processing)
    ├── 写入 Redis task:{task_id} 缓存
    ├── 推入 ARQ 任务队列
    └── 返回 202 {"task_id": "...", "status": "processing"}

ARQ Worker 消费任务
    │
    ├── 如果 source_type=url → 调用 scraper_client 抓取正文
    │   └── 抓取失败 → 更新 raw_infos (status=failed, error_msg=...)
    │
    ├── 调用 dify_client 执行 Workflow
    │   └── 调用失败 → 更新 raw_infos (status=failed, error_msg=...)
    │
    ├── Pydantic 校验 Dify 返回 JSON
    │   └── 校验失败 → 更新 raw_infos (status=parse_error, dify_raw_response=...)
    │
    ├── 写入 summary → raw_infos
    ├── 写入 action_items
    ├── 写入/关联 tags
    ├── 更新 raw_infos (status=done)
    └── 更新 Redis task:{task_id} 缓存
```

### 7.2 ARQ 任务定义

```python
async def process_digest(ctx: dict, task_id: str):
    ...
    return {"status": "done", "info_id": info_id}

class WorkerSettings:
    functions = [process_digest]
    redis_settings = RedisSettings(host="localhost", port=6379)
```

---

## 八、Pydantic 强校验设计

### 8.1 Dify 响应校验模型

```python
from pydantic import BaseModel, Field

class ActionItemOutput(BaseModel):
    content: str = Field(..., min_length=2, max_length=500)
    priority: str = Field(..., pattern="^(high|medium|low)$")

class DifyResponse(BaseModel):
    summary: str = Field(..., min_length=1, max_length=200)
    action_items: list[ActionItemOutput] = Field(..., min_length=1, max_length=10)
    tags: list[str] = Field(..., min_length=3, max_length=5)
```

### 8.2 校验失败处理策略

```python
try:
    result = DifyResponse.model_validate_json(raw_response)
except ValidationError as e:
    raw_info.status = "parse_error"
    raw_info.dify_raw_response = raw_response
    raw_info.error_msg = str(e)
    session.add(raw_info)
    await session.commit()
    logger.error(f"Dify response validation failed for task {task_id}: {e}")
    return
```

---

## 九、环境配置

### 9.1 环境变量（.env.example）

```env
# App
APP_NAME=Info-Butler
APP_ENV=development
DEBUG=true
API_KEY=your-api-key-here

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=info_butler
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=info_butler

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Dify
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=your-dify-api-key
DIFY_WORKFLOW_ID=your-workflow-id

# JWT (Phase 2)
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### 9.2 配置模型

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Info-Butler"
    app_env: str = "development"
    debug: bool = True
    api_key: str

    mysql_host: str
    mysql_port: int = 3306
    mysql_user: str
    mysql_password: str
    mysql_database: str

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    dify_api_url: str
    dify_api_key: str
    dify_workflow_id: str

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    class Config:
        env_file = ".env"
```

---

## 十、开发规范

### 10.1 代码风格

| 项目 | 规范 |
|------|------|
| Python 版本 | 3.12+ |
| 格式化工具 | ruff format |
| Lint 工具 | ruff check |
| 类型检查 | mypy（strict 模式） |
| Import 排序 | isort（ruff 内置） |
| 行宽 | 120 |
| 命名规范 | snake_case（变量/函数）、PascalCase（类）、UPPER_SNAKE（常量） |

### 10.2 Git 规范

**分支策略：**
- `main`：生产分支
- `dev`：开发分支
- `feature/*`：功能分支
- `fix/*`：修复分支

**Commit Message 格式：**
```
<type>(<scope>): <subject>

type: feat | fix | docs | refactor | test | chore
scope: api | model | service | worker | frontend | db
```

示例：
```
feat(api): add POST /api/v1/digest endpoint
fix(worker): handle Dify API timeout gracefully
refactor(service): extract tag creation to tag_service
```

### 10.3 测试规范

| 测试类型 | 工具 | 覆盖目标 |
|---------|------|---------|
| 单元测试 | pytest | Service 层逻辑 |
| API 测试 | pytest + httpx.AsyncClient | 接口契约 |
| 集成测试 | pytest + testcontainers | DB + Redis + Dify Mock |

**关键测试场景：**
- Dify 返回非标准 JSON → 校验失败 → 状态标记 parse_error
- URL 抓取失败 → 状态标记 failed
- 重复 URL 提交 → 返回已有记录
- 行动项状态流转 → pending → done / ignored

### 10.4 依赖管理（uv）

```bash
# 初始化项目
uv init

# 添加依赖
uv add fastapi uvicorn sqlalchemy aiomysql arq httpx readability-lxml pydantic-settings python-dotenv

# 添加开发依赖
uv add --dev pytest pytest-asyncio ruff mypy

# 安装依赖
uv sync
```

---

## 十一、部署方案

### 11.1 开发环境

```bash
# 启动 MySQL + Redis（Docker）
docker compose up -d mysql redis

# 启动后端
uv run uvicorn backend.main:app --reload --port 8000

# 启动 Worker
uv run arq backend.workers.worker.WorkerSettings

# 启动前端
cd frontend && npm run dev
```

### 11.2 Docker Compose（参考）

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: info_butler
      MYSQL_USER: info_butler
      MYSQL_PASSWORD: butler_pass
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  mysql_data:
```

### 11.3 生产部署

| 组件 | 方案 | 说明 |
|------|------|------|
| FastAPI | Uvicorn + Gunicorn | 多 Worker 进程 |
| ARQ Worker | systemd / Supervisor | 后台常驻 |
| MySQL | 云 RDS / 自建 | 定时备份 |
| Redis | 云 Redis / 自建 | 开启 AOF |
| Vue3 | Nginx 静态托管 | 构建后部署 |
| Dify | Cloud / Self-hosted | 按需选择 |

---

## 十二、开发路线图（详细任务拆解）

### Phase 1：MVP（核心闭环）

| # | 任务 | 涉及模块 | 依赖 |
|---|------|---------|------|
| 1.1 | uv 初始化项目 + 依赖安装 | 基础设施 | - |
| 1.2 | MySQL 建表 + Alembic 初始化 | DB | 1.1 |
| 1.3 | FastAPI 应用骨架 + 配置加载 | 后端 | 1.1 |
| 1.4 | ORM 模型定义（RawInfo, ActionItem, Tag） | 后端 | 1.2 |
| 1.5 | Pydantic Schema 定义 | 后端 | 1.4 |
| 1.6 | Dify Workflow 搭建 + 测试 | Dify | - |
| 1.7 | Dify Client 封装 | 后端 | 1.6 |
| 1.8 | Scraper Client 封装（URL 正文抓取） | 后端 | 1.1 |
| 1.9 | POST /api/v1/digest（同步版本） | 后端 | 1.5, 1.7, 1.8 |
| 1.10 | GET /api/v1/digest/{task_id} | 后端 | 1.9 |
| 1.11 | GET /api/v1/actions | 后端 | 1.5 |
| 1.12 | PATCH /api/v1/actions/{id} | 后端 | 1.5 |
| 1.13 | API Key 鉴权中间件 | 后端 | 1.3 |
| 1.14 | 端到端测试（HTTPie） | 测试 | 1.9-1.12 |

### Phase 2：业务化改造

| # | 任务 | 涉及模块 | 依赖 |
|---|------|---------|------|
| 2.1 | Redis 连接池 + ARQ 配置 | 后端 | Phase 1 |
| 2.2 | 同步改异步（ARQ 任务队列） | 后端 | 2.1 |
| 2.3 | Dify Workflow 升级（强制 JSON） | Dify | Phase 1 |
| 2.4 | Pydantic 强校验 + 异常队列 | 后端 | 2.3 |
| 2.5 | GET /api/v1/digest（列表 + 筛选） | 后端 | Phase 1 |
| 2.6 | GET /api/v1/tags | 后端 | Phase 1 |
| 2.7 | GET /api/v1/review/weekly | 后端 | 2.5 |
| 2.8 | Vue3 项目初始化 + 路由 | 前端 | - |
| 2.9 | 信息录入页 | 前端 | 2.8 |
| 2.10 | 知识卡片列表页 | 前端 | 2.8, 2.5 |
| 2.11 | 行动项看板 | 前端 | 2.8, 2.6 |
| 2.12 | 复盘仪表盘 | 前端 | 2.8, 2.7 |

### Phase 3：高级特性

| # | 任务 | 涉及模块 | 依赖 |
|---|------|---------|------|
| 3.1 | LangChain + FAISS 向量索引 | 后端 | Phase 2 |
| 3.2 | 语义检索 API | 后端 | 3.1 |
| 3.3 | 微信机器人 Webhook | 后端 | Phase 2 |
| 3.4 | 钉钉机器人 Webhook | 后端 | Phase 2 |
| 3.5 | 深色模式 | 前端 | Phase 2 |
| 3.6 | 标签热力图 + 趋势图 | 前端 | Phase 2 |
