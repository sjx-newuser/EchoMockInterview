"""
Echo Mock System - 动态记忆与上下文裁剪 (Sliding Window)
=========================================================
防止历史对话长度超出大模型上下文限制。保留最新的 N 轮对话，
同时可选保留最开始的“自我介绍”以防遗忘人设。
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class MemoryManager:
    """管理对话历史窗口"""

    def __init__(self, max_history_rounds: int = 6, keep_first_round: bool = True):
        """
        :param max_history_rounds: 滑动窗口大小，保留最近的 N 轮对话
        :param keep_first_round: 是否始终保留首轮对话（自我介绍）作为核心锚点
        """
        self.max_history_rounds = max_history_rounds
        self.keep_first_round = keep_first_round

    def build_context_window(self, histories: List[Dict[str, str]]) -> str:
        """
        将历史对话截断并拼装为供 LLM 阅读的纯文本格式。
        
        期望的 histories 格式为:
        [
            {"speaker": "AI", "content": "你好，请自我介绍", "round_seq": 0},
            {"speaker": "USER", "content": "我是一名开发...", "round_seq": 0},
            {"speaker": "AI", "content": "第二个问题...", "round_seq": 1},
            ...
        ]
        
        返回: 拼接好的历史对话字符串
        """
        if not histories:
            return "【暂无历史对话】"

        # 根据 round_seq 排序保障顺序
        sorted_hist = sorted(histories, key=lambda x: x.get("round_seq", 0))

        # 提取不同轮次的数据 (一个 round_seq 通常包含 1条 AI 和 1条 USER消息)
        rounds_data = {}
        for h in sorted_hist:
            r = h.get("round_seq", 0)
            if r not in rounds_data:
                rounds_data[r] = []
            rounds_data[r].append(h)

        all_rounds = sorted(list(rounds_data.keys()))
        rounds_to_keep = []

        if len(all_rounds) <= self.max_history_rounds:
            rounds_to_keep = all_rounds
        else:
            # 裁剪历史
            if self.keep_first_round and all_rounds:
                rounds_to_keep.append(all_rounds[0])
            
            # 取最近的 (max_history_rounds - 1) 个轮次
            tail_count = self.max_history_rounds - (1 if self.keep_first_round else 0)
            if tail_count > 0:
                recent_rounds = [r for r in all_rounds if r not in rounds_to_keep][-tail_count:]
                rounds_to_keep.extend(recent_rounds)

        rounds_to_keep = sorted(list(set(rounds_to_keep)))

        # 组装文本
        lines = []
        last_added_round = -1
        
        for r in rounds_to_keep:
            # 如果中间有跳跃，插入一个"省略"标识符
            if last_added_round != -1 and r - last_added_round > 1:
                lines.append("\n[...以上略去部分早期对话...]\n")
                
            for msg in rounds_data[r]:
                speaker_label = "面试官" if msg.get("speaker") == "AI" else "候选人"
                lines.append(f"[{speaker_label}]: {msg.get('content')}")
                
            last_added_round = r

        result = "\n".join(lines)
        if hasattr(logger, "debug"):
            logger.debug(f"[MemoryManager] 历史整理完毕，涉及轮次: {rounds_to_keep}")
        
        return result
