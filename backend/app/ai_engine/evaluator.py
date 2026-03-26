"""
Echo Mock System - 多维度考评与报告生成器
=========================================
融合大模型文本分析能力与旁路的语音特征，完成单题自动评分与最终面试报告生成。
内置容错解析机制，防止 LLM 返回的 JSON 格式不规范导致崩溃。
"""

import json
import re
import logging
from typing import Dict, List, Any

# 直接依赖我们在 AI Engine 目录下的 LLM 驱动
from app.ai_engine.llm_provider import llm_client
from app.ai_engine.rag.prompts import EVALUATION_PROMPT, COMPREHENSIVE_REPORT_PROMPT

logger = logging.getLogger(__name__)


def _extract_json_from_text(text: str) -> dict:
    """
    容错机制：大模型有时候会返回 ```json ... ``` 包装块，
    或者附加额外的描述语句，此方法负责提取干净的 JSON。
    """
    text = text.strip()
    
    # 尝试匹配 markdown json 块
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # 如果没有 markdown 块，直接尝试寻找大括号范围
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and start < end:
            json_str = text[start:end+1]
        else:
            json_str = text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"[Evaluator] JSON 解析失败! 原文: {text} | 异常: {e}")
        return {}


class InterviewEvaluator:
    """面试评估引擎"""

    async def evaluate_single_qa(
        self, question: str, user_answer: str, retrieved_standards: str
    ) -> Dict[str, Any]:
        """
        单题评分。
        给出一道题的得分和反馈。
        """
        logger.debug("[Evaluator] 开始进行单题评分...")
        # 确保全局 LLM 客户端加载了配置
        llm_client.init_app()

        prompt = EVALUATION_PROMPT.format(
            question=question,
            user_answer=user_answer or "（候选人未回答直接跳过或转写为空）",
            retrieved_standards=retrieved_standards or "参考答案为空，请基于业界通用标准评估"
        )

        try:
            raw_text = await llm_client.chat(prompt)
            data = _extract_json_from_text(raw_text)

            # 默认兜底值
            result = {
                "technical_score": float(data.get("technical_score", 0.0)),
                "correction_feedback": str(data.get("correction_feedback", "未生成有效反馈。"))
            }
            return result
        except Exception as e:
            logger.error(f"[Evaluator] 单题评分请求大模型异常: {e}")
            return {
                "technical_score": 0.0,
                "correction_feedback": f"评估功能遇到技术异常，无法给出具体反馈。异常信息: {str(e)}"
            }

    async def generate_comprehensive_report(
        self, target_role: str, dialogue_summary: str, evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        根据整场面试的历史数据，聚合文本评分与旁路计算出来的语音特征（语速、停顿等），
        生成雷达图结构与终局 Markdown 体验报告。
        
        :param target_role: 目标岗位 (如 Java开发工程师)
        :param dialogue_summary: 对话轮次概要
        :param evaluations: 混合多模态数值的数据。例如:
          [
             {
               "question": "...", "score": 85, "speech_rate": 180, "pause_ratio": 0.15
             }, ...
          ]
        """
        logger.info(f"[Evaluator] 开始生成【{target_role}】的综合报告...")
        llm_client.init_app()

        # 将 evaluations 数据扁平化整理为一个易读的指标文本，供大模型分析候选人的流畅度
        eval_details_str = ""
        for idx, ev in enumerate(evaluations, 1):
            q = ev.get("question", "未知问题")
            t_score = ev.get("score", 0.0)
            wpm = ev.get("speech_rate") or 0.0
            pause = ev.get("pause_ratio") or 0.0
            
            wpm_desc = "语速适中"
            if wpm > 250:
                wpm_desc = "语速偏快（紧张或熟练）"
            elif wpm > 0 and wpm < 120:
                wpm_desc = "语速较慢（思考中）"

            eval_details_str += (
                f"【第{idx}题】\n"
                f"- 问题: {q}\n"
                f"- 技术得分: {t_score}\n"
                f"- 发言体征: {wpm}字/分钟 ({wpm_desc})，异常停顿占比 {pause*100:.1f}%\n"
            )

        # 动态判定评估模型
        if "前端" in target_role:
            dimensions = ["技术深度", "交互审美与性能", "工程化视野", "沟通表达", "业务理解"]
        else:
            dimensions = ["技术深度", "架构设计与高可用", "系统排错能力", "沟通表达", "业务理解"]
            
        dim_list_str = "\n".join([f"- {d}" for d in dimensions])
        # 由于在模板外组装 JSON 字符串时不需要双大括号逃逸
        dim_json_str = ",\n".join([f'    {{"name": "{d}", "score": <number>}}' for d in dimensions])

        prompt = COMPREHENSIVE_REPORT_PROMPT.format(
            target_role=target_role,
            dimension_list=dim_list_str,
            dimension_json_format=dim_json_str,
            dialogue_summary=dialogue_summary or "无摘要",
            evaluation_details=eval_details_str or "未获取到有效答题明细。"
        )

        try:
            raw_text = await llm_client.chat(prompt)
            data = _extract_json_from_text(raw_text)
            
            # 使用兜底策略容错解析
            default_dims = [{"name": d, "score": 0} for d in dimensions]

            result = {
                "overall_score": float(data.get("overall_score", 0.0)),
                "dimension_scores": data.get("dimension_scores", default_dims),
                "report_markdown": data.get("report_markdown", "生成最终报告失败。")
            }
            return result
        except Exception as e:
            logger.error(f"[Evaluator] 生成综合报告异常: {e}")
            return {
                "overall_score": 0.0,
                "dimension_scores": [{"name": d, "score": 0} for d in dimensions],
                "report_markdown": f"报告生成器因技术异常中止：{str(e)}"
            }

# 单例导出
evaluator = InterviewEvaluator()
