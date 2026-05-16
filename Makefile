.PHONY: dev start stop logs clean install test help

# 默认目标
.DEFAULT_GOAL := help

# 开发环境启动（前后端）
dev:
	@echo "🚀 启动开发环境..."
	@uv run uvicorn backend.main:app --host 0.0.0.0 --port 9001 --reload &
	@cd frontend && npm run dev

# 仅启动后端
backend:
	@echo "🔧 启动后端..."
	@uv run uvicorn backend.main:app --host 0.0.0.0 --port 9001 --reload

# 仅启动前端
frontend:
	@echo "🎨 启动前端..."
	@cd frontend && npm run dev

# 安装所有依赖
install:
	@echo "📦 安装后端依赖..."
	@uv sync
	@echo "📦 安装前端依赖..."
	@cd frontend && npm install
	@echo "✅ 依赖安装完成"

# 运行测试
test:
	@echo "🧪 运行后端测试..."
	@uv run pytest
	@echo "🧪 运行前端测试..."
	@cd frontend && npm run test

# 代码检查
lint:
	@echo "🔍 后端代码检查..."
	@uv run ruff check backend/
	@echo "🔍 前端代码检查..."
	@cd frontend && npm run lint

# 数据库迁移
migrate:
	@echo "🗄️ 运行数据库迁移..."
	@uv run alembic upgrade head

# 清理缓存
clean:
	@echo "🧹 清理缓存..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .venv 2>/dev/null || true

# 帮助信息
help:
	@echo "Info-Butler 命令使用说明:"
	@echo ""
	@echo "  make dev        - 同时启动前后端开发服务器"
	@echo "  make backend    - 仅启动后端服务"
	@echo "  make frontend   - 仅启动前端服务"
	@echo "  make install    - 安装所有依赖"
	@echo "  make test       - 运行测试"
	@echo "  make lint       - 代码检查"
	@echo "  make migrate    - 数据库迁移"
	@echo "  make clean      - 清理缓存"
	@echo ""
	@echo "访问地址:"
	@echo "  前端: http://localhost:5175"
	@echo "  后端: http://localhost:9001"
	@echo "  API文档: http://localhost:9001/docs"
