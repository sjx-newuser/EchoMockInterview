"""
Echo Mock System - 数据库初始化脚本
====================================
运行方式（在 backend 目录下执行）：
    python scripts/init_db.py

功能：
    1. 根据 models.py 中的 ORM 定义，自动创建全部数据表。
    2. 若表已存在则跳过，不会破坏现有数据（使用 create_all）。
"""

import asyncio
import sys
import os

# 将项目根目录加入 Python 搜索路径，使脚本在任何目录下运行都能找到 app 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import engine
from app.db.models import Base


async def init_db():
    """异步创建全部数据表。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 关闭引擎释放连接池
    await engine.dispose()


def main():
    print("=" * 50)
    print("  Echo Mock System - 数据库初始化")
    print("=" * 50)
    print()
    print(f"[INFO] 数据库引擎: {engine.url}")
    print("[INFO] 开始创建表结构...")

    asyncio.run(init_db())

    print("[OK]   全部数据表创建成功！")
    print()
    print("  已创建的表：")
    for table_name in Base.metadata.tables:
        print(f"    ✔ {table_name}")
    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
