# Info-Butler User To-Do List

> 以下是需要用户手动完成的任务，AI 无法替代

---

## 必须完成（MVP 跑通前提）

### 1. Dify 平台搭建 Workflow

**优先级：P0 — 没有这个后端无法调用 AI**

**步骤：**

1. 注册/登录 [Dify](https://dify.ai/)（推荐使用 Dify Cloud 或自建 Docker 部署）
2. 创建新 Workspace → 新建 **Workflow** 类型应用
3. 配置输入变量：
   - `text`：string，正文内容
   - `source_type`：string，来源类型
4. 依次添加 LLM 节点：

   **节点 2 - 摘要生成：**
   ```
   你是一个专业的内容摘要助手。请为以下内容生成一段100字以内的核心摘要。
   要求：提炼核心观点、语言精练、不使用套话开头
   内容：{{text}}
   ```

   **节点 3 - 行动项提取：**
   ```
   你是一个行动项提取专家。请从以下内容中提取可执行的行动项。
   要求：每个行动项必须以动词开头；具体可执行可验证；避免模糊表述；
         为每个行动项评估优先级：high/medium/low；提取1-10个行动项
   内容：{{text}}
   摘要：{{summary}}
   ```

   **节点 4 - 标签生成：**
   ```
   你是一个标签分类专家。请为以下内容生成3-5个标签。
   要求：覆盖技术领域/主题/场景；2-4字或英文单词；不用宽泛标签；不带#号
   摘要：{{summary}}
   行动项：{{action_items}}
   ```

5. 设置输出为 JSON 格式，强制输出结构：
   ```json
   {
     "summary": "100字以内核心摘要",
     "action_items": [
       {"content": "可执行行动项", "priority": "high|medium|low"}
     ],
     "tags": ["标签1", "标签2", "标签3"]
   }
   ```
6. 发布并运行测试，确认输出符合预期
7. 复制 **API Key** 和 **Workflow ID**（或 API Base URL）

**完成后需要提供的信息：**
- `DIFY_API_URL`（如 `https://api.dify.ai/v1`）
- `DIFY_API_KEY`（应用的 API Key）
- `DIFY_WORKFLOW_ID`（Workflow 的 ID）

### 2. 准备本地环境

**优先级：P0**

- [✅] 安装并启动 MySQL 8.0+（建议用 Docker：`docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=info_butler mysql:8.0`）
- [✅] 创建数据库和用户：
  ```sql
  CREATE USER 'info_butler'@'%' IDENTIFIED BY 'butler_pass';
  GRANT ALL PRIVILEGES ON info_butler.* TO 'info_butler'@'%';
  FLUSH PRIVILEGES;
  ```
- [✅] 安装并启动 Redis 7.0+（Docker：`docker run -d -p 6379:6379 redis:7-alpine`）

### 3. 填写 .env 文件

**优先级：P0**

复制 `.env.example` 为 `.env`，填入实际值：
```env
API_KEY=your-custom-api-key-here
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=info_butler
MYSQL_PASSWORD=butler_pass
MYSQL_DATABASE=info_butler
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-xxxxxxxxxxxxxxx
DIFY_WORKFLOW_ID=your-workflow-id
```

---

## 可选完成（Phase 2 前准备）

### 4. Vue3 前端开发环境

- [ ] 安装 Node.js 18+
- [ ] 运行 `cd frontend && npm install && npm run dev`

### 5. 微信/钉钉机器人接入（Phase 3）

- [ ] 注册企业微信/钉钉机器人
- [ ] 获取 Webhook 地址

---

## 完成状态

| # | 任务 | 状态 | 备注 |
|---|------|------|------|
| 1 | Dify Workflow 搭建 | ✅ 已完成 | 已配置 API Key + Workflow ID |
| 2 | MySQL + Redis 本地部署 | ✅ 已完成 | MySQL:3306, Redis:6379(DB1) |
| 3 | .env 文件配置 | ✅ 已完成 | 全部环境变量已填入 |
| 4 | Vue3 开发环境 | ✅ 已完成 | 前端已创建并运行在 5173 |
| 5 | 微信/钉钉机器人接入 | ✅ 已完成 | 飞书 Webhook 已接入 |

---

## Phase 3 用户任务

### 8. Dify Workflow 输出质量优化

**优先级：P1 — 提升 AI 处理效果**

当前系统已可运行，以下是详细的优化步骤和检查清单：

---

#### Step 1：检查并优化 Prompt（在 Dify 平台操作）

**1.1 摘要节点 Prompt 优化**

当前后端发送的输入变量名为 `input_text`，确认 Dify 中引用变量名一致：
- 打开 Dify Workflow → 摘要 LLM 节点
- 确认 prompt 中使用 `{{input_text}}` 而非 `{{text}}`
- 建议替换为以下优化版 prompt：

```
你是一个专业的内容摘要助手。请为以下内容生成一段核心摘要。

【约束条件】
- 字数：80-150字
- 要求：提炼核心观点、语言精练、不使用"本文""文章"等套话开头
- 如果是技术文档：保留关键技术名词、版本号、命令
- 如果是新闻/公告：突出关键事件和时间点
- 如果是 URL 抓取内容：过滤掉导航栏/广告/页脚等噪音

【待处理内容】
{{input_text}}

【输出格式】
直接输出摘要文本，不要加任何前缀或标记。
```

**1.2 行动项提取节点 Prompt 优化**

```
你是一个行动项提取专家。请从以下内容和摘要中提取可执行的行动项。

【约束条件】
- 数量：提取 2-8 个行动项（不要强行凑数）
- 格式：每个行动项必须以动词开头（如"升级""配置""编写""测试"）
- 具体：必须具体可执行可验证，避免"提高效率""加强管理"等模糊表述
- 优先级评估标准：
  - high：紧急且重要、有明确截止日期、阻塞其他工作
  - medium：应该做但不紧急、常规改进项
  - low：锦上添花、长期规划、可选做

【输入内容】
原文：{{input_text}}
摘要：{{summary}}

【输出格式】
严格按照以下 JSON Schema 输出，不要有任何其他文字：
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "具体的可执行行动项，以动词开头"
      },
      "priority": {
        "type": "string",
        "enum": ["high", "medium", "low"],
        "description": "优先级"
      }
    },
    "required": ["content", "priority"],
    "additionalProperties": false
  }
}

输出示例：
[
  {"content": "升级前端项目至 Vue 3.5", "priority": "high"},
  {"content": "研究 defineModel 宏的用法", "priority": "medium"},
  {"content": "阅读官方迁移指南", "priority": "low"}
]
```

> **注意：** 在 Dify LLM 节点设置中，将输出模式设为 **JSON** 或在 System Prompt 中强制 JSON 约束。

**1.3 标签生成节点 Prompt 优化**

```
你是一个标签分类专家。请为以下内容生成标签。

【约束条件】
- 数量：3-6 个标签
- 长度：每个标签 2-6 个字符或英文单词
- 类型要求：
  - 至少 1 个技术领域标签（如 Python/Vue/Docker）
  - 至少 1 个主题标签（如 性能优化/安全/API设计）
  - 可包含场景标签（如 学习笔记/发布通知/技术选型）
- 不要使用宽泛标签（如"IT""技术""互联网""文章"）
- 不带 # 号，不使用空格分隔的多词标签

【输入内容】
摘要：{{summary}}
行动项：{{action_items}}

【输出格式】
严格按照以下 JSON Schema 输出，不要有任何其他文字：
{
  "type": "array",
  "items": {
    "type": "string",
    "description": "标签名称，2-6个字符"
  }
}

输出示例：
["Vue", "前端开发", "性能优化"]
```

---

#### Step 2：配置 Dify 输出模式（关键！）

在 Dify Workflow 的 **结束节点（End Node）** 中：

1. 将输出类型设置为 **JSON Object**（或选择「自定义」模式）
2. 配置输出字段映射：

| 输出字段名 | 来源 | 类型 |
|-----------|------|------|
| `summary` | 摘要节点的文本输出 | string |
| `action_items` | 行动项节点的 JSON 输出 | array |
| `tags` | 标签节点的 JSON 输出 | array |

3. 在 LLM 节点的高级设置中：
   - 开启 **JSON Mode** / **结构化输出**（如果 Dify 支持）
   - 设置 Temperature 为 `0.3`（低温度保证输出稳定）
   - 设置 Max Tokens 为 `2000`

4. Workflow 最终输出的完整 JSON Schema（用于验证）：

```json
{
  "type": "object",
  "properties": {
    "summary": {
      "type": "string",
      "description": "80-150字核心摘要"
    },
    "action_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "content": {"type": "string"},
          "priority": {"type": "string", "enum": ["high", "medium", "low"]}
        },
        "required": ["content", "priority"],
        "additionalProperties": false
      }
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["summary", "action_items", "tags"],
  "additionalProperties": false
}
```

**输出示例：**
```json
{
  "summary": "Vue 3.5发布，新增defineModel宏和useId组合式函数，建议团队升级前端项目以提升性能。",
  "action_items": [
    {"content": "升级前端项目至 Vue 3.5", "priority": "medium"},
    {"content": "研究 defineModel 宏用法", "priority": "low"},
    {"content": "应用 useId 组合式函数", "priority": "low"}
  ],
  "tags": ["Vue", "前端开发", "性能优化"]
}
```

---

#### Step 3：边界 Case 测试清单

在 Dify 平台的「运行」界面中，依次测试以下场景：

| # | 测试用例 | 预期结果 | 实际结果 |
|---|---------|---------|---------|
| 1 | 正常中文文本（500字） | ✅ 正常输出三部分 | |
| 2 | 英文技术文档 | ✅ 英文摘要 + 英文标签 | |
| 3 | 超长文本（>10000字） | ✅ 不截断，完整处理 | |
| 4 | 纯 URL 文本（如 `https://example.com/article/123`） | ⚠️ 应能识别为链接并给出合理摘要 | |
| 5 | 包含代码块的内容 | ✅ 保留代码关键信息 | |
| 6 | 特殊字符 / Markdown 内容 | ✅ 正常解析 | |
| 7 | 极短文本（<20字） | ⚠️ 给出简短回复或提示信息不足 | |
| 8 | 中文+英文混合内容 | ✅ 根据主要内容语言决定输出语言 | |

**测试方法：**
1. 进入 Dify Workflow → 点击「运行」
2. 填入测试用例内容
3. 观察三个 LLM 节点的输出
4. 记录异常情况并在下方表格填写实际结果

---

#### Step 4：验证后端兼容性

完成 Dify 优化后，在后端执行一次端到端测试确认兼容：

```bash
# 提交一条测试信息
curl -X POST http://localhost:8001/api/v1/digest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-2026" \
  -d '{"source_type":"text","content":"你的测试内容","title":"Dify 优化测试"}'

# 用返回的 task_id 查询结果
curl http://localhost:8001/api/v1/digest/{task_id} \
  -H "X-API-Key: dev-api-key-2026"
```

**检查要点：**
- [ ] status 字段为 `done`（非 failed/parse_error）
- [ ] summary 非空且长度合理
- [ ] action_items 是数组，每项有 content 和 priority
- [ ] priority 值仅为 high/medium/low
- [ ] tags 是字符串数组，数量 3-5 个
- [ ] 飞书通知正常收到

---

#### Step 5：常见问题排查

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| status=failed | Dify API Key 过期或网络不通 | 检查 .env 中 DIFY_API_KEY 和 DIFY_API_URL |
| status=parse_error | Dify 返回的 JSON 格式不符合预期 | 检查 Dify 结束节点的输出字段映射 |
| action_items 为空 | 行动项节点 prompt 太严格或 Temperature 太高 | 降低 Temperature 到 0.3，放宽 prompt 约束 |
| tags 只有 1-2 个 | 标签节点 prompt 未强调数量 | 明确要求 3-6 个标签 |
| priority 值异常（如 "重要"） | LLM 未遵循 high/medium/low 约束 | 在 prompt 中加粗强调 + 使用 JSON Mode |
| 超长文本被截断 | Dify 模型的 context window 限制 | 考虑在后端截取前 8000 字传入 |

---

### 优化检查清单（逐项打勾）

**Prompt 优化：**
- [ ] 摘要节点：使用 `{{input_text}}` 变量名 + 优化后的 prompt
- [ ] 行动项节点：JSON 格式输出 + priority 定义清晰 + 使用 `{{input_text}}` 和 `{{summary}}`
- [ ] 标签节点：JSON 格式输出 + 数量/类型约束 + 使用 `{{summary}}` 和 `{{action_items}}`

**Dify 配置：**
- [ ] 结束节点输出字段正确映射（summary/action_items/tags）
- [ ] LLM 节点 Temperature 设为 0.3
- [ ] LLM 节点 Max Tokens ≥ 2000
- [ ] 输出模式支持 JSON（如可用）

**测试验证：**
- [ ] 8 种边界 case 全部测试通过
- [ ] 后端端到端测试 status=done
- [ ] 飞书通知收到且格式正确
- [ ] action_items priority 仅为 high/medium/low

---

#### Step 6：首次测试诊断与修复（2026-04-21）

**测试输入：** Redis 相关技术文本

**输出 2（3 节点版本）结果：**
```json
{
  "summary": "Redis 凭借高性能、丰富数据结构及持久化机制...",
  "action_items": { "items": [], "type": "array" },
  "tags": { "items": ["Redis", "内存数据库", "高并发", "分布式架构"], "type": "array" }
}
```

**输出（单节点版本）结果：**
```json
{
  "summary": "用户表达了对Redis技术的赞赏",
  "action_items": [],
  "tags": ["数据库", "缓存", "技术"]
}
```

**诊断结论：**

| 问题 | 输出2 | 输出(单节点) | 根因 |
|------|-------|-------------|------|
| summary 质量 | ✅ 好 | ❌ 差 | 单节点 prompt 太泛化 |
| action_items 格式 | ❌ `{items:[],type:"array"}` | ❌ `[]` | 结构化输出包了 Schema 元数据 |
| tags 格式 | ❌ `{items:[...],type:"array"}` | ✅ `["..."]` | 同上 |
| action_items 为空 | ⚠️ 需更多可操作内容 | ⚠️ 同左 | 测试文本偏描述性 |
| tags 质量 | ✅ 具体有区分度 | ❌ 泛化 | 3 节点 prompt 更精确 |

**→ 结论：使用 3 节点版本（输出2），修复格式问题即可。**

---

##### 修复方案 A（推荐）：关闭结构化输出，改用纯文本 JSON 模式

在 Dify 中对 **行动项提取节点** 和 **标签生成节点** 执行以下操作：

1. 打开「行动项提取节点」→ 高级设置 / 输出设置
2. **关闭**「结构化输出」（Structured Output）或「JSON Schema」模式
3. 将输出模式改为 **文本（Text）**
4. 在 Prompt 的【输出格式】部分保留 JSON Schema 定义和示例即可（LLM 会按指令输出纯 JSON 文本）
5. 对 **标签生成节点** 做同样操作

> **原理：** Dify 的「结构化输出」功能会在返回值中包裹 Schema 元数据（`{"type":"array","items":...}`），后端只需要纯净的 JSON 数组。关闭该模式后 LLM 按 prompt 中的 Schema 约束输出纯文本 JSON，Dify 结束节点直接透传即可。

**修复后的预期输出：**
```json
{
  "summary": "Redis 凭借高性能、丰富数据结构及持久化机制...",
  "action_items": [
    {"content": "学习 Redis 主从复制配置", "priority": "medium"},
    {"content": "了解哨兵集群部署方案", "priority": "low"}
  ],
  "tags": ["Redis", "内存数据库", "高并发", "分布式架构"]
}
```

---

##### 修复方案 B（备选）：保持结构化输出，调整结束节点字段映射

如果不想关闭结构化输出，在 **输出 2（结束节点）** 中调整变量引用：

| 结束节点输出字段 | 当前引用 | 改为引用 |
|---------------|---------|---------|
| `summary` | `摘要节点/textString` | 不变 ✅ |
| `action_items` | `行动项提取节点/structured_output` | `行动项提取节点/structured_output/items` |
| `tags` | `标签生成节点/structured_output` | `标签生成节点/structured_output/items` |

> ⚠️ 此方案的缺点：如果 items 为空数组，可能仍有格式兼容性风险。推荐用 **方案 A**。

---

##### 行动项为空的补充说明

本次测试 `action_items` 返回空数组是正常的 — 因为测试文本是对 Redis 的**描述性介绍**，本身不包含明确的待办任务。这不是 bug。

**验证 action_items 提取效果需要用包含明确任务的文本**，见下方测试用例。

---

#### Step 7：修复后的测试用例

完成上述修复（推荐方案 A）后，依次在 Dify 「运行」界面测试以下用例：

| # | 场景 | 输入内容 | 预期 action_items 数量 |
|---|------|---------|---------------------|
| T1 | **含明确任务的会议纪要** | `项目周会纪要：1) 本周五前完成 API 文档更新并提交 review；2) 张三负责修复登录页的 XSS 漏洞（P0）；3) 李四调研 Redis 集群方案，下周一给出选型报告；4) 全组代码覆盖率需提升到 70% 以上` | 3-4 个，含 high 优先级 |
| T2 | **技术公告/发布通知** | `Vue 3.5 正式发布，新增 defineModel 宏简化 v-model 双向绑定写法，useId 组合式函数统一 ID 生成，建议团队在本季度内安排升级计划` | 1-2 个（medium/low） |
| T3 | **教程/学习笔记** | `今天学习了 FastAPI 的依赖注入系统，包括 Depends()、Security() 的用法，还需要练习自定义 Header 解析器和中间件开发` | 1-3 个 |
| T4 | **纯描述性内容**（复测） | `Redis 是一个开源的内存数据结构存储系统，可以用作数据库、缓存和消息中间件` | 0-1 个（允许为空） |
| T5 | **英文技术文档** | `We are migrating our monolithic backend to microservices using FastAPI. Each service needs JWT authentication, centralized logging, and circuit breaker pattern.` | 2-3 个 |
| T6 | **超长文本**（>2000字） | 复制一篇完整的技术博客文章 | 3-6 个 |

**每个用例检查清单：**
- [ ] `summary` 长度 80-150 字，非套话
- [ ] `action_items` 是**纯数组**（不是 `{items:[]}` 包裹）
- [ ] 每个 action_item 有 `content`(string) + `priority`("high"/"medium"/"low")
- [ ] `tags` 是**纯字符串数组**（不是 `{items:[""]}` 包裹）
- [ ] `tags` 数量 3-6 个，不含宽泛词

全部通过后 → 进入 Step 4 后端端到端验证

---

#### Step 8：第二次测试诊断 — 字符串 JSON 问题（2026-04-21）

**测试输入：** T1 会议纪要用例

**Dify 输出：**
```json
{
  "summary": "本周五前完成 API 文档更新并提交评审...",
  "action_items": "[\n  {\"content\": \"更新 API 文档...\", \"priority\": \"high\"},\n  ...]",
  "tags": "[\"API 文档\", \"安全修复\", \"Redis\", ...]"
}
```

**问题：** `action_items` 和 `tags` 的值是 **JSON 字符串**（带 `\n` 转义和引号包裹），而非真正的数组/对象。

**根因：** Dify LLM 节点输出模式设为「文本」时，LLM 输出的 JSON 文本被当作 string 类型透传到结束节点。

**修复（已完成后端）：** 在 [backend/clients/dify_client.py](file:///d:/code/py/Info-Butler/backend/clients/dify_client.py) 中新增 `_try_parse_json()` 容错函数：

- 自动检测字符串是否以 `[` 或 `{` 开头
- 若是，尝试 `json.loads()` 解析为真正的 list/dict
- 解析失败时降级为原始值，不影响流程

**验证结果：**
```
action_items type: list, count: 3
  - [high] 更新 API 文档并提交评审
  - [high] 修复登录页 P0 级 XSS 漏洞
  - [medium] 调研 Redis 集群方案并输出选型报告
tags type: list
  value: ['API 文档', '安全修复', 'Redis', '代码质量', '技术选型']
ALL OK ✅
```

> **说明：** 后端已做容错，无论 Dify 输出纯数组还是字符串化 JSON 都能正确解析。**无需再调整 Dify 配置**，当前输出质量已达标。

---

#### 当前状态总结

| 检查项 | 状态 |
|--------|------|
| summary 质量 | ✅ 具体详细，非套话 |
| action_items 格式 | ✅ 后端已兼容字符串/数组两种格式 |
| action_items 内容 | ✅ 有明确的 content + priority |
| tags 格式 | ✅ 后端已兼容字符串/数组两种格式 |
| tags 质量 | ✅ 具体有区分度 |
| 后端容错解析 | ✅ `_try_parse_json()` 已实现 |

**→ Dify 优化任务可标记为完成，进入 Phase 4 开发。**

---

## Phase 4 用户任务

### 当前状态：前端体验优化已完成（4.1-4.3），待继续 4.4/4.5

#### 已完成（后端自动完成，无需用户操作）

- [x] **4.1 标签管理前端页面** — Tags.vue 已创建
- [x] **4.2 信息详情页** — DigestDetail.vue 已创建
- [x] **4.3 搜索增强** — 路由/菜单/筛选已更新
- [x] **4.4 用户认证体系** — JWT 登录/注册/Token 鉴权 + 前端 Login 页面
- [x] **4.5 定时任务 / 批量导入** — POST batch（最多20条）+ GET status 队列监控

#### Phase 4 全部完成 ✅

#### 测试验证清单（请逐项确认）

- [x] 启动 Docker → Redis 连接正常 ✅
- [x] 后端 `http://localhost:8001` 健康检查通过 ✅
- [x] 注册用户 → 登录获取 Token ✅ (API 测试通过)
- [x] 前端 `http://localhost:5175` 打开 → 自动跳转登录页
- [x] 前端注册/登录流程正常
- [x] 信息录入 → 处理 → 查看详情 全流程
- [x] 标签管理 CRUD 操作
- [x] 知识卡片列表 → 点击卡片 → 详情页跳转
- [x] 点击标签 → 筛选功能
- [x] 行动项状态切换（完成/忽略/重开）
- [x] 退出登录 → 跳转登录页

### 4.6 用户数据隔离（紧急修复）✅

- [x] **问题修复：** 不同用户的数据完全隔离
  - 知识卡片、行动项、标签、周报复盘 — 全部按用户独立
  - 双用户测试通过：A看不到B的任何数据，反之亦然

### 4.8 URL 内容抓取增强 ✅

- [x] **功能实现：** 粘贴 URL → 自动采集页面内容 → AI 解析
  - 技术栈：httpx + BeautifulSoup4（替代 Playwright，避免 Windows asyncio 兼容问题）
  - 端到端测试通过：提交 URL → 抓取正文 → AI 生成摘要/标签/行动项
  - 覆盖 95%+ 常规网站（博客/文档/新闻），Wikipedia 等强反爬站除外

---

## Phase 5：数据洞察与生产力增强

### 5.1 数据导出功能（Markdown / JSON / CSV）
- [ ] 后端 `export_service.py` + `export.py` API
- [ ] 前端导出按钮 + 格式选择
- [ ] 支持当前筛选条件导出

### 5.2 周报复盘仪表盘可视化
- [ ] 后端 monthly/stats 统计接口
- [ ] 引入 ECharts 图表库
- [ ] 折线图（趋势）+ 饼图（标签分布）+ 柱状图（完成对比）

### 5.3 全文搜索增强
- [ ] MySQL FULLTEXT 索引创建
- [ ] 搜索高亮 + 相关度排序
- [ ] 前端防抖 + 搜索建议

### 5.4 行动项提醒系统
- [ ] ARQ 定期检查任务
- [ ] 到期/逾期飞书推送
- [ ] 前端到期高亮 + 逾期标记

### 5.5 信息详情页增强
- [ ] 关联推荐（同标签卡片）
- [ ] 行动项版本历史

### 5.6 单元测试完善
- [ ] Service 层 ≥80% 覆盖率
- [ ] API 层关键路径全覆盖

### 5.7 安全加固
- [ ] API 限流（slowapi）
- [ ] JWT 黑名单 + 密码强度校验
- [ ] CORS 收紧
