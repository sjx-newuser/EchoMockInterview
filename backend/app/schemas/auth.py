"""
Echo Mock System - 鉴权相关 Pydantic 模型
"""

from pydantic import BaseModel, Field


# =============================================
# 请求模型 (前端 -> 后端)
# =============================================

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="明文密码")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="明文密码")


# =============================================
# 响应模型 (后端 -> 前端)
# =============================================

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT 令牌")
    token_type: str = Field(default="bearer")


class UserInfo(BaseModel):
    id: str = Field(..., description="用户 UUID")
    username: str = Field(..., description="用户名")

    class Config:
        from_attributes = True
