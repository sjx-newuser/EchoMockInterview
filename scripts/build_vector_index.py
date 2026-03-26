"""
Echo Mock System - 离线向量索引构建脚本
========================================
运行方式（在项目根目录下执行）：
    python scripts/build_vector_index.py

功能：
    解析 data/raw/ 下的 Markdown/PDF/TXT 文件，
    分块后分别灌入 ChromaDB 的 questions_col 和 standards_col。

约定：
    - 文件名含 "answer" 或 "standard" → standards_col（评判标准链路）
    - 其余文档 → questions_col（出题链路）
"""

import sys
import os
import logging

# 将 backend 目录加入 Python 搜索路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

from app.ai_engine.rag.indexer import build_all_indexes
from app.core.config import settings


def main():
    print("=" * 60)
    print("  Echo Mock System - 向量索引构建")
    print("=" * 60)
    print()
    print(f"[INFO] 原始题库目录: {settings.RAW_DATA_DIR}")
    print(f"[INFO] ChromaDB 存储: {settings.CHROMA_PERSIST_DIR}")
    print(f"[INFO] 出题集合:     {settings.CHROMA_QUESTIONS_COLLECTION}")
    print(f"[INFO] 标准集合:     {settings.CHROMA_STANDARDS_COLLECTION}")
    print(f"[INFO] Embedding:    {settings.EMBEDDING_MODEL_NAME}")
    print()

    if not settings.EMBEDDING_API_KEY:
        print("[WARNING] EMBEDDING_API_KEY 未配置！请在 .env 中设置后重试。")
        print("          示例: EMBEDDING_API_KEY=sk-xxxx")
        sys.exit(1)

    build_all_indexes()

    print()
    print("=" * 60)
    print("  构建完成 ✔")
    print("=" * 60)


if __name__ == "__main__":
    main()
