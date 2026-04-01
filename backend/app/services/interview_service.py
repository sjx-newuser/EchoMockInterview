"""
Echo Mock System - 面试场次服务层
==================================
封装一切与 InterviewSession 相关的数据库增删改查。
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import InterviewSession


class InterviewService:
    @staticmethod
    async def create_session(db: AsyncSession, user_id: int, target_role: str) -> InterviewSession:
        session = InterviewSession(user_id=user_id, target_role=target_role)
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def get_user_sessions(db: AsyncSession, user_id: int) -> List[InterviewSession]:
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.start_time.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_session_detail(db: AsyncSession, session_id: str, user_id: int) -> Optional[InterviewSession]:
        result = await db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.messages))
            .where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str, user_id: int) -> bool:
        """删除面试场次。由于设置了 cascade='all, delete-orphan'，关联的消息和评估明细会自动删除。"""
        session = await InterviewService.get_session_detail(db, session_id, user_id)
        if not session:
            return False
        
        await db.delete(session)
        await db.flush()
        return True

    @staticmethod
    async def toggle_favorite(db: AsyncSession, session_id: str, user_id: int) -> Optional[InterviewSession]:
        """切换收藏状态。"""
        session = await InterviewService.get_session_detail(db, session_id, user_id)
        if not session:
            return None
        
        session.is_favorite = not session.is_favorite
        await db.flush()
        return session
