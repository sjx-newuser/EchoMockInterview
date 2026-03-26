"""
Echo Mock System - SQLite 异步数据库引擎
=========================================
使用 aiosqlite 驱动，开启 WAL 模式以支持高并发读写。
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import event

# ------------------------------------
# 数据库路径配置
# ------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "echo_mock.db")

# 确保 data 目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# ------------------------------------
# 创建异步引擎
# ------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # 生产环境关闭 SQL 日志；调试时可设为 True
    future=True,
    connect_args={
        "check_same_thread": False,  # SQLite 必须关闭同线程检查以配合异步
    },
)


# ------------------------------------
# 开启 WAL 模式
# ------------------------------------
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """
    每次底层原始连接建立时，通过 PRAGMA 开启 WAL 日志模式。
    WAL (Write-Ahead Logging) 允许读写并发，显著提升 FastAPI 多协程场景下的吞吐量。
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")   # SQLite 默认不强制外键，必须手动开启
    cursor.execute("PRAGMA synchronous=NORMAL;")  # WAL 模式下 NORMAL 已足够安全且更快
    cursor.close()


# ------------------------------------
# 会话工厂
# ------------------------------------
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象，避免惰性加载在异步上下文中报错
)


async def get_db() -> AsyncSession:
    """
    FastAPI 依赖注入用：获取一个异步数据库会话。
    使用方式：
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
