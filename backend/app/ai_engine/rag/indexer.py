"""
Echo Mock System - 数据流式入库与分块处理
==========================================
负责解析 data/raw/ 下的 Markdown/PDF 文件，
按策略分块后分别灌入 ChromaDB 的 questions_col 和 standards_col。

使用 LlamaIndex 的 SimpleDirectoryReader + SentenceSplitter 完成。
"""

import os
import logging
from typing import List, Optional

from llama_index.core import Document, Settings as LlamaSettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_chroma_client() -> chromadb.ClientAPI:
    """获取 ChromaDB 持久化客户端。"""
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_embedding_model() -> OpenAIEmbedding:
    """构建 Embedding 模型实例（使用 OpenAI 兼容接口）。"""
    return OpenAIEmbedding(
        api_key=settings.EMBEDDING_API_KEY,
        api_base=settings.EMBEDDING_BASE_URL,
        model_name=settings.EMBEDDING_MODEL_NAME,
    )


def load_documents(directory: str, required_exts: Optional[List[str]] = None) -> List[Document]:
    """
    从指定目录递归加载文档。
    支持 .md / .pdf / .txt 等格式。
    """
    if not os.path.exists(directory):
        logger.warning(f"目录不存在，跳过加载: {directory}")
        return []

    exts = required_exts or [".md", ".pdf", ".txt"]
    reader = SimpleDirectoryReader(
        input_dir=directory,
        recursive=True,
        required_exts=exts,
    )
    docs = reader.load_data()
    logger.info(f"从 {directory} 加载了 {len(docs)} 个文档")
    return docs


def split_documents(documents: List[Document], chunk_size: int = 512, chunk_overlap: int = 64) -> list:
    """
    对文档进行语义感知分块。
    - chunk_size: 每块的最大 token 数
    - chunk_overlap: 块间重叠 token 数（保证上下文连续性）
    """
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(documents)
    logger.info(f"分块完成: {len(documents)} 个文档 -> {len(nodes)} 个节点")
    return nodes


def index_to_chroma(
    nodes: list,
    collection_name: str,
    embedding_model: Optional[OpenAIEmbedding] = None,
):
    """
    将分块后的节点向量化并存入 ChromaDB。

    Args:
        nodes: LlamaIndex 分块后的节点列表
        collection_name: ChromaDB 集合名称（questions_col 或 standards_col）
        embedding_model: Embedding 模型实例
    """
    embed_model = embedding_model or _get_embedding_model()
    client = _get_chroma_client()

    # 获取或创建集合
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
    )

    # 批量计算 Embedding 并写入
    batch_size = 32
    total = len(nodes)

    for i in range(0, total, batch_size):
        batch = nodes[i : i + batch_size]

        texts = [node.get_content() for node in batch]
        ids = [node.node_id for node in batch]
        metadatas = [
            {
                "file_name": node.metadata.get("file_name", ""),
                "file_path": node.metadata.get("file_path", ""),
            }
            for node in batch
        ]

        # 调用 Embedding 模型获取向量
        embeddings = embed_model.get_text_embedding_batch(texts)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info(f"[{collection_name}] 已写入 {min(i + batch_size, total)}/{total} 个节点")

    logger.info(f"[{collection_name}] 索引构建完成，共 {collection.count()} 条记录")


def build_all_indexes():
    """
    一键构建全部向量索引。
    遍历 data/raw/ 下的各子目录，将文档分别灌入 questions_col 和 standards_col。

    约定：
    - 文件名含 "answer" 或 "standard" 的文档 → standards_col（评判标准链路）
    - 其余文档 → questions_col（出题链路）
    """
    embed_model = _get_embedding_model()
    raw_dir = settings.RAW_DATA_DIR

    if not os.path.exists(raw_dir):
        logger.error(f"原始题库目录不存在: {raw_dir}")
        return

    question_docs = []
    standard_docs = []

    # 遍历 raw 目录下的所有子目录
    all_docs = load_documents(raw_dir)

    for doc in all_docs:
        file_name = doc.metadata.get("file_name", "").lower()
        if "answer" in file_name or "standard" in file_name:
            standard_docs.append(doc)
        else:
            question_docs.append(doc)

    logger.info(f"分类完成: {len(question_docs)} 个出题文档, {len(standard_docs)} 个标准答案文档")

    # 分块 + 入库: 出题链路
    if question_docs:
        q_nodes = split_documents(question_docs)
        index_to_chroma(q_nodes, settings.CHROMA_QUESTIONS_COLLECTION, embed_model)

    # 分块 + 入库: 评判标准链路
    if standard_docs:
        s_nodes = split_documents(standard_docs)
        index_to_chroma(s_nodes, settings.CHROMA_STANDARDS_COLLECTION, embed_model)

    logger.info("全部向量索引构建完成 ✔")
