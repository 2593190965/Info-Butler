# 飞书机器人配置指南

## 快速开始（5分钟完成配置）

### 步骤 1：创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用信息：
   - 应用名称：`Info-Butler`（或您喜欢的名称）
   - 应用描述：`智能信息管家`
   - 应用图标：上传一个图标

### 步骤 2：获取应用凭证

创建完成后，在「凭证与基础信息」页面可以看到：

- **App ID**: `cli_xxxxxxxxxxxx`
- **App Secret**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

将这两个值复制下来。

### 步骤 3：配置应用权限

在「权限管理」页面，开通以下权限：

**必需权限**：
- ✅ `im:message` - 接收消息
- ✅ `im:message:send_as_bot` - 以应用身份发消息
- ✅ `contact:user.base:readonly` - 获取用户基本信息

**可选权限**：
- `im:chat` - 获取群组信息
- `contact:user.email:readonly` - 获取用户邮箱

### 步骤 4：配置事件订阅

1. 在「事件订阅」页面，开启事件订阅
2. 填写请求网址：
   ```
   http://your-server-ip:8001/api/v1/webhook/feishu
   ```

   **注意**：
   - 如果是本地开发，需要使用内网穿透工具（如 ngrok）
   - 如果是云服务器，确保端口 8001 可访问

3. 订阅以下事件：
   - ✅ `im.message.receive_v1` - 接收消息

4. 保存后，系统会验证 URL 有效性
5. 验证成功后，获取以下信息：
   - **Encrypt Key**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Verification Token**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 步骤 5：发布应用

1. 在「版本管理与发布」页面
2. 创建版本并提交审核
3. 审核通过后，添加应用到企业

---

## 配置环境变量

将获取的配置填入 `.env` 文件：

```env
# 飞书机器人配置
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/3b41aca1-8ff3-4b30-bd8c-86af6307ba1b
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_ENCRYPT_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_VERIFICATION_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_REMINDER_ADVANCE_DAYS=1
```

**配置说明**：
- `FEISHU_WEBHOOK_URL`: Webhook 推送地址（已有）
- `FEISHU_APP_ID`: 应用 ID（从步骤 2 获取）
- `FEISHU_APP_SECRET`: 应用密钥（从步骤 2 获取）
- `FEISHU_ENCRYPT_KEY`: 加密密钥（从步骤 4 获取）
- `FEISHU_VERIFICATION_TOKEN`: 验证令牌（从步骤 4 获取）
- `FEISHU_REMINDER_ADVANCE_DAYS`: 提前提醒天数（默认 1）

---

## 本地开发配置（内网穿透）

如果您的应用运行在本地，需要使用内网穿透工具让飞书能访问到您的服务。

### 方案 1：使用 ngrok

```bash
# 安装 ngrok
# 访问 https://ngrok.com 注册并下载

# 启动内网穿透
ngrok http 8001

# 会显示类似：
# Forwarding  https://abc123.ngrok.io -> http://localhost:8001
```

使用 `https://abc123.ngrok.io/api/v1/webhook/feishu` 作为事件订阅 URL。

### 方案 2：使用 frp

```bash
# 安装 frp
# 配置 frpc.ini

[common]
server_addr = your-frp-server.com
server_port = 7000

[feishu-webhook]
type = http
local_ip = 127.0.0.1
local_port = 8001
custom_domains = feishu.your-domain.com
```

使用 `http://feishu.your-domain.com/api/v1/webhook/feishu` 作为事件订阅 URL。

---

## 测试机器人

配置完成后，测试机器人是否正常：

### 测试 1：URL 验证

```bash
curl -X POST http://localhost:8001/api/v1/webhook/feishu \
  -H "Content-Type: application/json" \
  -d '{
    "type": "url_verification",
    "token": "your-verification-token",
    "challenge": "test-challenge"
  }'
```

预期响应：
```json
{
  "challenge": "test-challenge"
}
```

### 测试 2：发送消息

在飞书中：
1. 找到刚创建的机器人
2. @机器人发送：`帮助`
3. 应该收到使用说明

### 测试 3：添加待办

```
@机器人 帮我添加一个待办，下午一点要去买眼镜
```

预期响应：
```
✅ 信息处理完成

📝 摘要
下午一点去买眼镜

📋 行动项:
1. 🟡 下午一点去买眼镜
```

---

## 常见问题

### Q1: 提示"URL 验证失败"

**原因**：飞书无法访问到您的服务器

**解决方案**：
1. 检查服务器防火墙，确保端口 8001 开放
2. 检查应用是否正在运行
3. 查看应用日志，是否有验证请求到达

### Q2: 消息发送失败

**原因**：权限不足或 token 失效

**解决方案**：
1. 检查是否开通了 `im:message:send_as_bot` 权限
2. 检查 App ID 和 App Secret 是否正确
3. 查看日志中的错误信息

### Q3: 收不到消息回调

**原因**：事件订阅配置错误

**解决方案**：
1. 检查事件订阅是否开启
2. 确认已订阅 `im.message.receive_v1` 事件
3. 检查 Encrypt Key 和 Verification Token 是否正确

### Q4: Token 过期

**原因**：tenant_access_token 有效期 2 小时

**解决方案**：
- 系统会自动刷新 token，无需手动处理
- 如果频繁失败，检查 App Secret 是否正确

---

## 最小化配置（仅接收消息）

如果您只需要机器人能接收和回复消息，最小配置：

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- Encrypt Key 和 Verification Token 是可选的（用于安全验证）
- Webhook URL 是可选的（用于主动推送通知）

---

## 完整功能检查清单

- [ ] 创建飞书应用
- [ ] 获取 App ID 和 App Secret
- [ ] 开通消息接收和发送权限
- [ ] 配置事件订阅 URL
- [ ] 订阅 `im.message.receive_v1` 事件
- [ ] 获取 Encrypt Key 和 Verification Token
- [ ] 配置环境变量
- [ ] 重启应用
- [ ] 测试机器人功能

---

## 下一步

配置完成后：

1. 重启应用：`stop.bat` → `start.bat`
2. 在飞书中测试机器人
3. 查看 [FEISHU_BOT_USAGE.md](./FEISHU_BOT_USAGE.md) 了解更多用法
4. 查看 [FEISHU_ACCOUNT_BINDING.md](./FEISHU_ACCOUNT_BINDING.md) 了解账号关联

---

## 获取帮助

如遇问题：
- 查看应用日志
- 检查飞书开放平台文档
- 提交 GitHub Issue
