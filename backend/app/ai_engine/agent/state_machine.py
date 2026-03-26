"""
Echo Mock System - Agent 状态机与生命周期管理
==============================================
负责根据对话轮次和进度，将面试划分为破冰、简历深挖、技术基础、场景设计、反问等阶段，
并动态加载对应的 System Prompt。
"""

import logging
from typing import Tuple

from app.ai_engine.rag.prompts import STAGE_PROMPTS

logger = logging.getLogger(__name__)


class InterviewStage:
    ICEBREAK = "icebreak"
    RESUME_DIVE = "resume_dive"
    FUNDAMENTALS = "fundamentals"
    SCENARIO = "scenario"
    REVERSE_QA = "reverse_qa"


class InterviewStateMachine:
    """被动状态机（无状态计算器），根据当前轮次计算状态"""

    def __init__(self, target_role: str):
        self.target_role = target_role

    def get_current_stage(self, current_round: int) -> str:
        """
        根据 AI 和 USER 对话的轮次（round_seq 的最大值）判断当前阶段。
        规则 (可灵活调整)：
        - 0-1 轮：破冰与自我介绍
        - 2-4 轮：简历深挖
        - 5-9 轮：技术基础连环问
        - 10-12 轮：场景设计题
        - >=13 轮：反问环节
        """
        if current_round <= 1:
            return InterviewStage.ICEBREAK
        elif current_round <= 4:
            return InterviewStage.RESUME_DIVE
        elif current_round <= 9:
            return InterviewStage.FUNDAMENTALS
        elif current_round <= 12:
            return InterviewStage.SCENARIO
        else:
            return InterviewStage.REVERSE_QA

    def get_stage_prompt(self, current_round: int, retrieved_context: str = "") -> Tuple[str, str]:
        """
        获取当前阶段的标识和构建好的 Prompt。
        对于需要 RAG 知识支撑的阶段，需要传入 retrieved_context。
        
        返回: (stage_name, prompt_string)
        """
        stage = self.get_current_stage(current_round)
        prompt_template = STAGE_PROMPTS.get(stage, STAGE_PROMPTS[InterviewStage.ICEBREAK])

        # 针对需要植入外部知识的特殊阶段进行格式化
        if stage in (InterviewStage.FUNDAMENTALS, InterviewStage.SCENARIO):
            prompt = prompt_template.format(retrieved_questions=retrieved_context or "暂无参考题目，请根据目标岗位自由提问。")
        else:
            prompt = prompt_template

        logger.debug(f"[StateMachine] 计算得出当前阶段: {stage} (Round {current_round})")
        return stage, prompt
