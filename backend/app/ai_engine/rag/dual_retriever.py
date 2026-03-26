"""
Echo Mock System - 双链路检索器
================================
提供两条独立的 RAG 检索链路：
1. **出题链路 (questions_col)**：从面试题库中检索相关题目，供面试官主动发问。
2. **评判标准链路 (standards_col)**：从优秀回答范例中检索参考答案，供系统比对评判。

使用 LlamaIndex 的 VectorStoreIndex + ChromaVectorStore 封装。
"""

import logging
from typing import List, Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


class DualRetriever:
    """
    双链路检索器。
    - retrieve_questions(): 检索面试题目（出题用）
    - retrieve_standards(): 检索参考答案（评判用）
    """

    def __init__(self):
        self._chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._embed_model = OpenAIEmbedding(
            api_key=settings.EMBEDDING_API_KEY,
            api_base=settings.EMBEDDING_BASE_URL,
            model_name=settings.EMBEDDING_MODEL_NAME,
        )

        # 惰性初始化索引（首次调用时创建）
        self._question_index: Optional[VectorStoreIndex] = None
        self._standard_index: Optional[VectorStoreIndex] = None

    def _get_index(self, collection_name: str) -> VectorStoreIndex:
        """从 ChromaDB 集合构建 LlamaIndex 向量索引。"""
        collection = self._chroma_client.get_or_create_collection(name=collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self._embed_model,
        )

    @property
    def question_index(self) -> VectorStoreIndex:
        if self._question_index is None:
            self._question_index = self._get_index(settings.CHROMA_QUESTIONS_COLLECTION)
        return self._question_index

    @property
    def standard_index(self) -> VectorStoreIndex:
        if self._standard_index is None:
            self._standard_index = self._get_index(settings.CHROMA_STANDARDS_COLLECTION)
        return self._standard_index

    def retrieve_questions(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[NodeWithScore]:
        """
        出题链路：根据当前对话上下文检索相关面试题目。

        Args:
            query: 检索查询文本（通常为当前对话摘要或岗位关键词）
            top_k: 返回最相关的 N 个结果

        Returns:
            按相似度排序的检索结果列表
        """
        retriever = self.question_index.as_retriever(similarity_top_k=top_k)
        results = retriever.retrieve(query)
        logger.info(f"[出题链路] query='{query[:50]}...', 检索到 {len(results)} 条结果")
        return results

    def retrieve_standards(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[NodeWithScore]:
        """
        评判标准链路：根据面试题目检索对应的优秀回答范例。

        Args:
            query: 检索查询文本（通常为 AI 提出的面试问题原文）
            top_k: 返回最相关的 N 个结果

        Returns:
            按相似度排序的参考答案列表
        """
        retriever = self.standard_index.as_retriever(similarity_top_k=top_k)
        results = retriever.retrieve(query)
        logger.info(f"[评判链路] query='{query[:50]}...', 检索到 {len(results)} 条结果")
        return results

    @staticmethod
    def format_results(results: List[NodeWithScore]) -> str:
        """将检索结果格式化为可直接嵌入 Prompt 的文本块。"""
        if not results:
            return "（无检索结果）"

        formatted_parts = []
        for i, node_with_score in enumerate(results, 1):
            text = node_with_score.node.get_content().strip()
            score = node_with_score.score or 0.0
            source = node_with_score.node.metadata.get("file_name", "未知来源")
            formatted_parts.append(
                f"【结果 {i}】(相似度: {score:.3f}, 来源: {source})\n{text}"
            )

        return "\n\n".join(formatted_parts)


# 全局单例（在应用生命周期内复用连接）
dual_retriever = DualRetriever()
