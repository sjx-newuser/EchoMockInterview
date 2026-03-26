"""
Echo Mock System - JWT 签发与密码哈希
======================================
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# ------------------------------------
# 密码哈希配置
# ------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """将明文密码转化为 bcrypt 哈希。"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码是否匹配哈希。"""
    return pwd_context.verify(plain_password, hashed_password)


# ------------------------------------
# JWT 配置
# ------------------------------------
SECRET_KEY = "echo-mock-system-secret-key-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 默认 24 小时


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """签发 JWT 令牌，payload 中携带 user_id (sub)。"""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """
    解码 JWT 令牌，返回 user_id。
    令牌无效或过期时返回 None。
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
