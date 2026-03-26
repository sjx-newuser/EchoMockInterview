"""
Echo Mock System - 评估器 (Evaluator) 单元测试
==============================================
完全 mock 掉大模型的 HTTP 依赖，测试对各种脏数据 JSON 的容错解析
以及正常的评分流程。
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.ai_engine.evaluator import _extract_json_from_text, InterviewEvaluator

# =============================================
# 1. 测试容错 JSON 解析函数 _extract_json_from_text
# =============================================

class TestJsonExtraction:
    def test_pure_json(self):
        text = '{"technical_score": 85.0, "correction_feedback": "很好"}'
        data = _extract_json_from_text(text)
        assert data["technical_score"] == 85.0

    def test_markdown_code_block_json(self):
        text = '''
        这里是前置废话
        ```json
        {
          "technical_score": 90,
          "correction_feedback": "非常棒"
        }
        ```
        这是后置废话
        '''
        data = _extract_json_from_text(text)
        assert data["technical_score"] == 90
        assert data["correction_feedback"] == "非常棒"

    def test_fuzzy_brackets_without_markdown(self):
        text = '好的，我的评分如下。\n {\n    "technical_score": 60,\n    "correction_feedback": "一般般"\n  } \n希望对你有帮助。'
        data = _extract_json_from_text(text)
        assert data["technical_score"] == 60

    def test_invalid_json_returns_empty_dict(self):
        text = '这是一段完全没有 JSON 的胡言乱语'
        data = _extract_json_from_text(text)
        assert data == {}


# =============================================
# 2. 测试 InterviewEvaluator 单题评估
# =============================================

class TestInterviewEvaluatorSingleQA:
    @pytest.fixture
    def evaluator(self):
        return InterviewEvaluator()

    @pytest.mark.asyncio
    @patch('app.ai_engine.evaluator.llm_client')
    async def test_evaluate_single_qa_success(self, mock_llm_client, evaluator):
        mock_llm_client.chat = AsyncMock()
        mock_llm_client.chat.return_value = '```json\n{"technical_score": 95.0, "correction_feedback": "完美回答"}\n```'

        result = await evaluator.evaluate_single_qa("什么是IOC？", "IOC就是控制反转", "参考标准在这里")
        
        mock_llm_client.init_app.assert_called_once()
        assert result["technical_score"] == 95.0
        assert result["correction_feedback"] == "完美回答"

    @pytest.mark.asyncio
    @patch('app.ai_engine.evaluator.llm_client')
    async def test_evaluate_single_qa_fallback_on_error(self, mock_llm_client, evaluator):
        # 模拟大模型抛出网络断开异常
        mock_llm_client.chat = AsyncMock()
        mock_llm_client.chat.side_effect = Exception("API Server timeout")

        result = await evaluator.evaluate_single_qa("题", "答", "标")

        assert result["technical_score"] == 0.0
        assert "API Server timeout" in result["correction_feedback"]


# =============================================
# 3. 测试 InterviewEvaluator 报告生成
# =============================================

class TestInterviewEvaluatorReport:
    @pytest.fixture
    def evaluator(self):
        return InterviewEvaluator()

    @pytest.mark.asyncio
    @patch('app.ai_engine.evaluator.llm_client')
    async def test_generate_comprehensive_report_success(self, mock_llm_client, evaluator):
        # 模拟 LLM 返回完整的报告架构
        mock_response = MagicMock()
        mock_response.text = '''
        {
          "overall_score": 82.5,
          "dimension_scores": [
            {"name": "技术深度", "score": 85},
            {"name": "逻辑表达", "score": 80}
          ],
          "report_markdown": "## 综合评价\\n候选人表现不错"
        }
        '''
        mock_llm_client.chat = AsyncMock()
        mock_llm_client.chat.return_value = mock_response.text
        
        evaluations = [
            {"question": "Q1", "score": 88, "speech_rate": 200, "pause_ratio": 0.05},
            {"question": "Q2", "score": 75, "speech_rate": 80, "pause_ratio": 0.3}
        ]

        result = await evaluator.generate_comprehensive_report("全栈开发", "对话了几轮", evaluations)
        
        # 验证提示词内部逻辑已被触发
        args, kwargs = mock_llm_client.chat.call_args
        prompt_used = args[0]
        
        # 断言融合了音频特征
        assert "200字/分钟" in prompt_used
        assert "异常停顿占比 30.0%" in prompt_used
        
        # 断言结果
        assert result["overall_score"] == 82.5
        assert len(result["dimension_scores"]) == 2
        assert "候选人表现不错" in result["report_markdown"]
