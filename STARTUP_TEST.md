# 启动脚本测试清单

## ✅ 测试步骤

### 1. 测试 PowerShell 脚本

```powershell
# 打开 PowerShell
# 导航到项目目录
cd D:\code\py\Info-Butler

# 执行启动脚本
.\start.ps1
```

**预期结果：**
- ✅ 打开两个新窗口（Backend 和 Frontend）
- ✅ 后端窗口显示：`Uvicorn running on http://0.0.0.0:8001`
- ✅ 前端窗口显示：`Local: http://localhost:5175/`
- ✅ 原窗口显示访问地址

**如果出现权限错误：**
```powershell
# 临时允许运行脚本
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 然后重新运行
.\start.ps1
```

---

### 2. 测试批处理脚本

```bash
# 双击 start.bat
# 或在命令行执行
start.bat
```

**预期结果：**
- ✅ 打开两个新窗口
- ✅ 后端窗口显示：`Uvicorn running on http://0.0.0.0:8001`
- ✅ 前端窗口显示：`Local: http://localhost:5175/`
- ✅ 无乱码，无错误信息

---

### 3. 测试 npm scripts

```bash
# 首次使用需安装依赖
npm install

# 启动
npm run dev
```

**预期结果：**
- ✅ 单窗口显示前后端日志
- ✅ 后端日志蓝色，前端日志绿色
- ✅ Ctrl+C 可停止服务

---

### 4. 验证服务正常

**浏览器访问：**
- 前端：http://localhost:5175
- 后端 API：http://localhost:8001/docs
- 健康检查：http://localhost:8001/health

**预期结果：**
- ✅ 前端页面正常加载
- ✅ API 文档可访问
- ✅ 健康检查返回 `{"status": "ok"}`

---

### 5. 测试停止脚本

**PowerShell：**
```powershell
.\stop.ps1
```

**批处理：**
```bash
stop.bat
```

**预期结果：**
- ✅ 两个窗口自动关闭
- ✅ 进程已终止（检查任务管理器）

---

## 🐛 常见问题排查

### Q1: PowerShell 提示"无法运行脚本"

**解决方案：**
```powershell
# 临时允许（推荐）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 或永久允许（管理员权限）
Set-ExecutionPolicy RemoteSigned
```

---

### Q2: 批处理脚本报错"系统找不到指定的路径"

**解决方案：**
```bash
# 确保在项目根目录运行
# 应该能看到 backend\ 和 frontend\ 目录
dir backend\main.py
dir frontend\package.json
```

---

### Q3: 端口被占用

**查看端口占用：**
```bash
# Windows
netstat -ano | findstr :8001
netstat -ano | findstr :5175

# 结束占用进程（替换 PID）
taskkill /PID <进程ID> /F
```

---

### Q4: uv 命令找不到

**解决方案：**
```bash
# 检查是否安装
uv --version

# 如果未安装
pip install uv

# 或使用 pip 启动（替代方案）
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

---

## 📊 性能对比

| 启动方式 | 启动时间 | 内存占用 | 窗口数 |
|---------|---------|---------|--------|
| PowerShell | ~5秒 | ~300MB | 2个 |
| 批处理 | ~5秒 | ~300MB | 2个 |
| npm scripts | ~5秒 | ~300MB | 1个 |
| PM2 | ~5秒 | ~250MB | 0个（后台） |

---

## ✅ 推荐配置

### 开发环境
- **首选：** PowerShell 脚本（彩色输出，易读）
- **备选：** 批处理脚本（兼容性好）

### 生产环境
- **推荐：** PM2 进程管理（自动重启，监控）

### 团队协作
- **推荐：** npm scripts（统一前端团队习惯）

---

## 🎯 快速验证清单

- [ ] PowerShell 脚本可正常启动
- [ ] 批处理脚本可正常启动
- [ ] npm scripts 可正常启动
- [ ] 前端页面可访问
- [ ] API 文档可访问
- [ ] 健康检查正常
- [ ] 停止脚本可正常关闭服务

全部通过则说明启动脚本配置成功！🎉
