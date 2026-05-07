# Info-Butler 快速启动指南

## 🚀 一键启动方式

### 方式 1：批处理脚本（推荐 Windows 用户）

**启动服务：**
```bash
# 双击运行或在终端执行
start.bat
```

**停止服务：**
```bash
# 双击运行或在终端执行
stop.bat
```

**特点：**
- ✅ 开启两个独立窗口，方便查看日志
- ✅ 关闭脚本窗口后服务继续运行
- ✅ 无需安装额外依赖

---

### 方式 2：npm scripts（单窗口）

**首次使用需安装依赖：**
```bash
npm install
```

**启动服务：**
```bash
npm run dev
```

**停止服务：**
```bash
# Windows
npm run stop

# 或按 Ctrl+C
```

**特点：**
- ✅ 单窗口查看前后端日志
- ✅ 前后端日志用不同颜色区分
- ✅ 类似前端项目习惯

**需要先安装：**
```bash
npm install --save-dev concurrently
```

---

### 方式 3：PM2 进程管理（生产级）

**首次使用需安装 PM2：**
```bash
npm install -g pm2
```

**启动服务：**
```bash
pm2 start ecosystem.config.js
```

**查看日志：**
```bash
pm2 logs
```

**停止服务：**
```bash
pm2 stop all
```

**重启服务：**
```bash
pm2 restart all
```

**特点：**
- ✅ 后台运行，关闭终端不影响
- ✅ 自动重启，崩溃恢复
- ✅ 支持监控和日志管理
- ✅ 适合生产环境

---

### 方式 4：Makefile（跨平台）

**启动服务：**
```bash
make dev
```

**其他命令：**
```bash
make install    # 安装所有依赖
make test       # 运行测试
make lint       # 代码检查
make migrate    # 数据库迁移
make clean      # 清理缓存
make help       # 查看所有命令
```

**特点：**
- ✅ Linux/macOS/Windows Git Bash 通用
- ✅ 命令简洁易记
- ✅ 可扩展性强

**Windows 用户需要：**
- 安装 [Make for Windows](http://gnuwin32.sourceforge.net/packages/make.htm)
- 或使用 Git Bash 运行

---

## 📋 访问地址

启动成功后访问：

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5175 |
| 后端 API | http://localhost:8001 |
| API 文档 | http://localhost:8001/docs |
| 健康检查 | http://localhost:8001/health |

---

## 🔧 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+
- Redis 7.0+
- uv（Python 包管理器）

---

## 🆘 常见问题

### Q: 启动失败怎么办？

**检查环境：**
```bash
# 检查 Python 版本
python --version

# 检查 Node.js 版本
node --version

# 检查 uv 是否安装
uv --version

# 检查 MySQL 和 Redis 是否运行
# Windows: 服务管理器中查看
# Linux: systemctl status mysql redis
```

### Q: 端口被占用怎么办？

**查看端口占用：**
```bash
# Windows
netstat -ano | findstr :8001
netstat -ano | findstr :5175

# Linux/macOS
lsof -i :8001
lsof -i :5175
```

**修改端口：**
- 后端：修改 `start.bat` 中的 `--port 8001`
- 前端：修改 `frontend/vite.config.ts` 中的 `server.port`

### Q: 如何后台运行？

使用 PM2 方式：
```bash
pm2 start ecosystem.config.js
pm2 save        # 保存进程列表
pm2 startup     # 开机自启动
```

---

## 🎯 推荐方案

| 场景 | 推荐方案 |
|------|----------|
| 日常开发 | `start.bat` 或 `npm run dev` |
| 团队协作 | `Makefile` |
| 生产部署 | `PM2` |
| CI/CD | `npm run dev` |

---

## 📝 手动启动（不推荐）

如果以上方式都不可用，可以手动启动：

**终端 1 - 后端：**
```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

---

更多配置请参考 [README.md](./README.md)
