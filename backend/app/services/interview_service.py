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
