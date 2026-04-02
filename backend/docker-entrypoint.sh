#!/bin/bash
set -e

echo "=========================================="
echo "  Echo Mock System - Docker Entrypoint   "
echo "=========================================="

# 确保 data 目录存在并有权限
mkdir -p /app/data

# 自动初始化数据库表结构
echo "[Init] 正在检查并初始化数据库表结构..."
python scripts/init_db.py

# 启动应用
echo "[Start] 正在启动 FastAPI 后端服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
