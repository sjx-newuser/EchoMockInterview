"""
Echo Mock System - 报告业务层
================================
专门负责 AI 面试报告的懒加载触发生成。
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from datetime import datetime
from app.db.models import InterviewSession, SessionStatus
from app.ai_engine.evaluator import evaluator


class ReportService:
    @staticmethod
    async def get_or_generate_report(db: AsyncSession, session_id: str, user_id: int) -> Optional[InterviewSession]:
        """
        获取指定面试场次数据。如果综合报告未生成，则聚拢数据唤醒大模型进行实时分析落库。
        """
        result = await db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.evaluations))
            .where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # 懒汉式生成防抖
        if not session.comprehensive_report:
            flat_evals = []
            for ev in session.evaluations:
                flat_evals.append({
                    "question": ev.question_content,
                    "score": ev.technical_score,
                    "speech_rate": ev.speech_rate,
                    "pause_ratio": ev.pause_ratio
                })
                
            res = await evaluator.generate_comprehensive_report(
                target_role=session.target_role,
                dialogue_summary="共经历了完整轮次的对话",  
                evaluations=flat_evals
            )
            
            session.overall_score = res.get("overall_score")
            session.dimension_scores = res.get("dimension_scores")
            session.comprehensive_report = res.get("report_markdown")
            session.status = SessionStatus.COMPLETED
            session.end_time = datetime.utcnow()
            
            await db.commit()
            await db.refresh(session)

        return session
