"""
Echo Mock System - 报告相关 Pydantic 模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """单维度评分项 - 供 ECharts 雷达图消费"""
    name: str = Field(..., description="维度名称（如：技术深度、逻辑表达、沟通能力）")
    score: float = Field(..., ge=0, le=100, description="该维度得分（0-100）")


class QaEvaluationItem(BaseModel):
    """单道问答的评估明细"""
    id: str
    question_content: str
    user_answer: Optional[str] = None
    audio_analysis_status: str
    speech_rate: Optional[float] = None
    pause_ratio: Optional[float] = None
    technical_score: Optional[float] = None
    correction_feedback: Optional[str] = None

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """完整的面试报告响应"""
    session_id: str
    target_role: str
    status: str
    overall_score: Optional[float] = None
    dimension_scores: Optional[List[DimensionScore]] = None
    comprehensive_report: Optional[str] = None
    evaluations: List[QaEvaluationItem] = []
