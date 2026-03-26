"""
Echo Mock System - 报告路由
============================
GET /api/v1/reports/{session_id}  - 获取面试综合报告（含雷达图维度与问答明细）
基于 ReportService 轻薄化处理。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.report import ReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["评估报告"])


@router.get("/{session_id}", response_model=ReportResponse)
async def get_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    获取指定面试场次的综合评估报告。
    """
    session = await ReportService.get_or_generate_report(db, session_id, user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试场次不存在",
        )

    return ReportResponse(
        session_id=session.id,
        target_role=session.target_role,
        status=session.status.value if session.status else "UNKNOWN",
        overall_score=session.overall_score,
        dimension_scores=session.dimension_scores,
        comprehensive_report=session.comprehensive_report,
        evaluations=session.evaluations,
    )
