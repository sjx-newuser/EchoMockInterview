"""
Echo Mock System - Agent 模块单元测试
=====================================
覆盖: state_machine.py / memory.py
"""

import pytest
from app.ai_engine.agent.state_machine import InterviewStateMachine, InterviewStage
from app.ai_engine.agent.memory import MemoryManager

# =============================================
# 1. State Machine 测试
# =============================================

class TestInterviewStateMachine:
    def setup_method(self):
        self.sm = InterviewStateMachine(target_role="后端工程师")

    def test_stage_transitions(self):
        """测试根据轮次流转面试阶段"""
        assert self.sm.get_current_stage(0) == InterviewStage.ICEBREAK
        assert self.sm.get_current_stage(1) == InterviewStage.ICEBREAK
        assert self.sm.get_current_stage(2) == InterviewStage.RESUME_DIVE
        assert self.sm.get_current_stage(4) == InterviewStage.RESUME_DIVE
        assert self.sm.get_current_stage(5) == InterviewStage.FUNDAMENTALS
        assert self.sm.get_current_stage(9) == InterviewStage.FUNDAMENTALS
        assert self.sm.get_current_stage(10) == InterviewStage.SCENARIO
        assert self.sm.get_current_stage(12) == InterviewStage.SCENARIO
        assert self.sm.get_current_stage(13) == InterviewStage.REVERSE_QA
        assert self.sm.get_current_stage(99) == InterviewStage.REVERSE_QA

    def test_get_stage_prompt_normal(self):
        """测试获取普通阶段的 Prompt"""
        stage, prompt = self.sm.get_stage_prompt(0)
        assert stage == InterviewStage.ICEBREAK
        assert "【破冰阶段】" in prompt

    def test_get_stage_prompt_with_rag(self):
        """测试需要注入 RAG 上下文的 Prompt"""
        retrieved = "1. 什么是 Redis 雪崩？"
        stage, prompt = self.sm.get_stage_prompt(5, retrieved_context=retrieved)
        
        assert stage == InterviewStage.FUNDAMENTALS
        assert "【检索到的参考题目】" in prompt
        assert "Redis 雪崩" in prompt


# =============================================
# 2. Memory Manager 测试
# =============================================

class TestMemoryManager:
    def test_empty_history(self):
        manager = MemoryManager()
        assert manager.build_context_window([]) == "【暂无历史对话】"

    def test_small_history_kept_intact(self):
        """记录数小于最大限制，应被全量保留"""
        manager = MemoryManager(max_history_rounds=3)
        history = [
            {"speaker": "AI", "content": "你好", "round_seq": 0},
            {"speaker": "USER", "content": "你好，我是张三", "round_seq": 0},
            {"speaker": "AI", "content": "有什么技能", "round_seq": 1},
            {"speaker": "USER", "content": "Java", "round_seq": 1},
        ]
        
        result = manager.build_context_window(history)
        
        assert "[面试官]: 你好" in result
        assert "[候选人]: 你好，我是张三" in result
        assert "[面试官]: 有什么技能" in result
        assert "[候选人]: Java" in result
        # 不应有跳跃标识
        assert "[...以上略去部分早期对话...]" not in result

    def test_history_sliding_window_with_first_kept(self):
        """超出限制时，保留第一轮，截断中间部分，保留最近的部分"""
        manager = MemoryManager(max_history_rounds=3, keep_first_round=True)
        # 伪造 5 轮对话
        history = []
        for i in range(5):
            history.append({"speaker": "AI", "content": f"AI问回合{i}", "round_seq": i})
            history.append({"speaker": "USER", "content": f"User答回合{i}", "round_seq": i})
            
        result = manager.build_context_window(history)
        
        # 应该保留 round 0 (首轮)
        assert "[面试官]: AI问回合0" in result
        # 应该保留 round 3, 4 (由于 max=3, 包含首部 1 个，还剩 2 个名额)
        assert "[面试官]: AI问回合1" not in result
        assert "[面试官]: AI问回合2" not in result
        assert "[...以上略去部分早期对话...]" in result
        assert "[面试官]: AI问回合3" in result
        assert "[面试官]: AI问回合4" in result

    def test_history_sliding_window_without_first_kept(self):
        """超出限制时，如果不保留首轮，仅截断前面的部分"""
        manager = MemoryManager(max_history_rounds=2, keep_first_round=False)
        history = []
        for i in range(5):
            history.append({"speaker": "AI", "content": f"AI问回合{i}", "round_seq": i})
            history.append({"speaker": "USER", "content": f"User答回合{i}", "round_seq": i})
            
        result = manager.build_context_window(history)
        
        assert "[面试官]: AI问回合0" not in result
        assert "[面试官]: AI问回合1" not in result
        assert "[面试官]: AI问回合2" not in result
        assert "[...以上略去部分早期对话...]" not in result  # 因为前面没有任何保留的，全是最新的，所以并没有中间跳跃断层
        assert "[面试官]: AI问回合3" in result
        assert "[面试官]: AI问回合4" in result
