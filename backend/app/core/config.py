"""
Echo Mock System - 全局环境变量配置
====================================
集中管理 LLM API、ChromaDB 路径、Redis URL 等核心配置。
通过 .env 文件注入，Pydantic Settings 自动读取。
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    项目核心配置项。
    优先读取环境变量或 .env 文件，未配置时使用默认值。
    """

    # ----------------------------------
    # 大模型 API 配置（留空，部署时通过 .env 注入）
    # ----------------------------------
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL_NAME: str = ""       # 默认模型名称，可按需替换

    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_MODEL_NAME: str = ""  # 默认 Embedding 模型

    # ----------------------------------
    # ChromaDB 向量数据库配置
    # ----------------------------------
    # 项目根目录 = backend 的上一级
    _PROJECT_ROOT: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )

    CHROMA_PERSIST_DIR: str = os.path.join(_PROJECT_ROOT, "data", "vector_store")
    CHROMA_QUESTIONS_COLLECTION: str = "questions_col"   # 面试题与考点（用于系统主动发问）
    CHROMA_STANDARDS_COLLECTION: str = "standards_col"   # 优秀回答范例与底层逻辑（用于评判）

    # ----------------------------------
    # 原始题库数据目录
    # ----------------------------------
    RAW_DATA_DIR: str = os.path.join(_PROJECT_ROOT, "data", "raw")

    # ----------------------------------
    # JWT 与安全
    # ----------------------------------
    SECRET_KEY: str = "echo-mock-system-secret-key-change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 小时

    # ----------------------------------
    # SQLite 数据库路径
    # ----------------------------------
    DATABASE_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "echo_mock.db"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ),
            ".env"
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 全局单例
settings = Settings()
