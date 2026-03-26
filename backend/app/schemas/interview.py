"""
Echo Mock System - 面试场次相关 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================
# 请求模型 (前端 -> 后端)
# =============================================

class InterviewCreateRequest(BaseModel):
    target_role: str = Field(..., description="目标岗位（如 Java 后端、前端）")


# =============================================
# 响应模型 (后端 -> 前端)
# =============================================

class InterviewBrief(BaseModel):
    """面试场次摘要 - 用于列表展示"""
    id: str
    target_role: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    overall_score: Optional[float] = None

    class Config:
        from_attributes = True


class InterviewDetail(BaseModel):
    """面试场次详情 - 包含完整对话与评分"""
    id: str
    target_role: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    overall_score: Optional[float] = None
    dimension_scores: Optional[Dict[str, Any]] = None
    comprehensive_report: Optional[str] = None
    messages: List["MessageItem"] = []

    class Config:
        from_attributes = True


class MessageItem(BaseModel):
    """单条对话消息"""
    id: str
    round_seq: int
    speaker: str
    content: str
    audio_file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
