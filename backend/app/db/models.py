"""
Echo Mock System - 数据库表结构定义
===================================
包含四张核心业务表：
1. users             - 用户信息表
2. interview_sessions - 面试场次表（聚合层）
3. dialogue_messages  - 对话流水表（交互层）
4. qa_evaluations     - 问答评估明细表（异步融合层）
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.types import JSON


def _generate_uuid() -> str:
    """生成 UUID 字符串，作为跨数据库兼容的主键默认值。"""
    return str(uuid.uuid4())
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# =============================================
# 枚举类型定义
# =============================================

class SessionStatus(str, enum.Enum):
    """面试场次状态：进行中 / 评估中 / 已完成"""
    ONGOING = "ONGOING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"


class SpeakerRole(str, enum.Enum):
    """对话说话人角色：AI 面试官 / 用户"""
    AI = "AI"
    USER = "USER"


class AudioAnalysisStatus(str, enum.Enum):
    """后台音频特征计算状态：等待 / 计算中 / 完成"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


# =============================================
# 1. 用户信息表 (users)
# 定位：系统的基石，用于关联历史数据，支撑"成长曲线"的可视化。
# =============================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_generate_uuid, comment="唯一标识")
    username = Column(String(64), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(256), nullable=False, comment="加密后的密码")
    created_at = Column(DateTime, default=datetime.utcnow, comment="账号注册时间")

    # 关联关系
    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# =============================================
# 2. 面试场次表 (interview_sessions) - 聚合层
# 定位：管理单次面试的完整生命周期，作为最终雷达图和综合报告的数据源。
# =============================================

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=_generate_uuid, comment="面试场次唯一标识")
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False, comment="关联到具体用户")
    target_role = Column(String(128), nullable=False, comment="目标岗位（如 Java 后端、前端）")
    status = Column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.ONGOING,
        nullable=False,
        comment="状态（进行中、评估中、已完成）",
    )
    start_time = Column(DateTime, default=datetime.utcnow, comment="面试开始时间")
    end_time = Column(DateTime, nullable=True, comment="面试结束时间")
    overall_score = Column(Float, nullable=True, comment="综合总分（面试完成后计算）")
    dimension_scores = Column(JSON, nullable=True, comment="多维度能力得分（结构化数据，供 ECharts 渲染）")
    comprehensive_report = Column(Text, nullable=True, comment="大模型生成的最终整体评价与建议")
    is_favorite = Column(Boolean, default=False, comment="是否收藏")

    # 关联关系
    user = relationship("User", back_populates="sessions")
    messages = relationship("DialogueMessage", back_populates="session", cascade="all, delete-orphan")
    evaluations = relationship("QaEvaluation", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InterviewSession(id={self.id}, role='{self.target_role}', status={self.status.value})>"


# =============================================
# 3. 对话流水表 (dialogue_messages) - 交互层
# 定位：支撑主干道 WebSocket 的极速读写，完整复盘对话上下文，不做任何阻塞操作。
# =============================================

class DialogueMessage(Base):
    __tablename__ = "dialogue_messages"

    id = Column(String(36), primary_key=True, default=_generate_uuid, comment="消息唯一标识")
    session_id = Column(String(36), ForeignKey("interview_sessions.id"), index=True, nullable=False, comment="所属面试场次")
    round_seq = Column(Integer, nullable=False, comment="对话轮次序号（用于前端按序渲染）")
    speaker = Column(
        Enum(SpeakerRole, name="speaker_role"),
        nullable=False,
        comment="说话人角色（AI 或 USER）",
    )
    content = Column(Text, nullable=False, comment="转换后的文本内容")
    audio_file_path = Column(String(512), nullable=True, comment="原始录音文件的本地或对象存储路径")
    created_at = Column(DateTime, default=datetime.utcnow, comment="消息产生时间")

    # 关联关系
    session = relationship("InterviewSession", back_populates="messages")

    def __repr__(self):
        return f"<DialogueMessage(id={self.id}, round={self.round_seq}, speaker={self.speaker.value})>"


# =============================================
# 4. 问答评估明细表 (qa_evaluations) - 异步融合层
# 定位：连接大模型文本评价与本地特征分析的桥梁。旁路任务算完数据后静默更新此表。
# =============================================

class QaEvaluation(Base):
    __tablename__ = "qa_evaluations"

    id = Column(String(36), primary_key=True, default=_generate_uuid, comment="评估记录唯一标识")
    session_id = Column(String(36), ForeignKey("interview_sessions.id"), index=True, nullable=False, comment="所属面试场次")
    question_content = Column(Text, nullable=False, comment="AI 提出的具体问题")
    user_answer = Column(Text, nullable=True, comment="用户的最终文本回答")
    audio_analysis_status = Column(
        Enum(AudioAnalysisStatus, name="audio_analysis_status"),
        default=AudioAnalysisStatus.PENDING,
        nullable=False,
        comment="后台音频计算状态（等待、计算中、完成）",
    )
    speech_rate = Column(Float, nullable=True, comment="语速特征（字/分钟，异步写入）")
    pause_ratio = Column(Float, nullable=True, comment="停顿占比特征（异步写入）")
    technical_score = Column(Float, nullable=True, comment="文本维度的技术准确度得分（大模型生成）")
    correction_feedback = Column(Text, nullable=True, comment="针对该题的具体纠错与改进建议")

    # 关联关系
    session = relationship("InterviewSession", back_populates="evaluations")

    def __repr__(self):
        return f"<QaEvaluation(id={self.id}, status={self.audio_analysis_status.value})>"
