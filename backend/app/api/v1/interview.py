"""
Echo Mock System - 面试场次路由
================================
基于 Services 层轻薄化处理！
POST /api/v1/interviews/            - 创建面试场次
GET  /api/v1/interviews/            - 获取当前用户的面试历史列表
GET  /api/v1/interviews/{session_id} - 获取单个场次详情（含对话记录）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.interview import InterviewBrief, InterviewCreateRequest, InterviewDetail
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["面试场次"])


@router.post("/", response_model=InterviewBrief, status_code=status.HTTP_201_CREATED)
async def create_interview(
    body: InterviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建一个新的面试场次。"""
    return await InterviewService.create_session(db, user.id, body.target_role)


@router.get("/", response_model=list[InterviewBrief])
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前用户的全部面试历史（按时间倒序）。"""
    return await InterviewService.get_user_sessions(db, user.id)


@router.get("/{session_id}", response_model=InterviewDetail)
async def get_interview_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取单个面试场次的详细信息，包含完整对话记录。"""
    session = await InterviewService.get_session_detail(db, session_id, user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试场次不存在",
        )
    return session
