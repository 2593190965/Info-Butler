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
| 5 | 微信/钉钉机器人接入 | ⬜ 待完成 | Phase 3+ 需要 |

---

## Phase 3 用户任务

### 8. Dify Workflow 输出质量优化

**优先级：P1 — 提升 AI 处理效果**

当前系统已可运行，建议优化以提升输出质量：
- [ ] 检查 Dify Workflow 的 prompt 是否合理（摘要/行动项/标签三个节点）
- [ ] 测试边界 case：超长文本（>10000字）、特殊字符、纯 URL、空内容
- [ ] 调整输出格式约束，确保 JSON 结构稳定
- [ ] 确认 action_items 中 priority 字段始终为 high/medium/low
- [ ] 测试中文/英文混合内容的处理效果
