"""
Echo Mock System - 全局大模型驱动提供者 (AI Engine / Providers)
================================================================
使用 OpenAI-compatible AsyncClient 适配第三方代理端点 (如 aihubmix)。
"""

import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """全局统一的 LLM 客户端基座 (OpenAI-compatible)"""

    def __init__(self):
        self._is_ready = False
        self._client: AsyncOpenAI | None = None
        self._model_name: str = ""

    def init_app(self):
        """应用启动时调用，或者首次调用时懒加载初始化"""
        if self._is_ready:
            return

        api_key = settings.LLM_API_KEY
        if not api_key:
            logger.warning("[LLM] 未配置 LLM_API_KEY，大模型服务将不可用。")
            return

        logger.info("[LLM] 正在初始化项目全局大模型核心 (OpenAI-compatible)...")

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.LLM_BASE_URL or "https://api.openai.com/v1",
        )
        self._model_name = settings.LLM_MODEL_NAME or "gpt-4o"
        self._is_ready = True
        logger.info(f"[LLM] 大模型底座加载完成: model={self._model_name}, base_url={settings.LLM_BASE_URL}")

    async def chat_stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """
        全双工流式生成响应 (Typing Effect 核心)。
        """
        self.init_app()

        if not self._client:
            yield "【系统提示：未配置大模型 API_KEY】"
            return

        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"[LLM] 全局生成异常: {e}")
            yield f"[AI 引擎错误]: 大模型断连，{e}"

    async def chat(self, prompt: str) -> str:
        """
        非流式生成响应（用于评估等不需要打字机效果的场景）。
        """
        self.init_app()

        if not self._client:
            return "【系统提示：未配置大模型 API_KEY】"

        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"[LLM] 非流式生成异常: {e}")
            return f"[AI 引擎错误]: {e}"


# 单例导出供全局使用
llm_client = LLMClient()
