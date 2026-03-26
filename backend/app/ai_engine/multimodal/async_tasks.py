"""
Echo Mock System - 异步后台分析任务 (Slow Path)
==============================================
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import QaEvaluation, AudioAnalysisStatus
from app.ai_engine.multimodal.express import analyze_audio_expression

logger = logging.getLogger(__name__)

async def analyze_and_save_audio_metrics(
    db: AsyncSession,
    eval_id: str,
    audio_bytes: bytes,
    asr_text: str
):
    """
    后台任务处理管道：
    1. 调用 Librosa 提取多维量化特征
    2. 落库对应的 QaEvaluation 记录（用于生成最终报告雷达图）
    """
    try:
        if not eval_id:
            logger.warning("[AsyncTask] 缺少 eval_id，跳过 DB 落库")
            return

        # 1. Librosa cpu密集型特征提取
        metrics = analyze_audio_expression(audio_bytes, asr_text)

        # 2. 存入数据库
        # 注意: 如果这里是后台任务(BackgroundTasks)，应确保使用传入的独立 db session，或自行创建。
        # 假设上层（ws.py）管理了协程的 Session
        db_eval = await db.get(QaEvaluation, eval_id)
        if db_eval:
            db_eval.speech_rate = metrics["wpm"]
            db_eval.pause_ratio = metrics["pause_ratio"]
            db_eval.audio_analysis_status = AudioAnalysisStatus.COMPLETED
            # 其它硬核特征如 RMS、Pitch 可存入扩展 JSON 字段或另建字段
            await db.commit()
            logger.info(f"[AsyncTask] 分析结果已落库 eval_id: {eval_id}")
        else:
            logger.warning(f"[AsyncTask] 未找到对应的评估记录: {eval_id}")

    except Exception as e:
        logger.error(f"[AsyncTask] 执行严重异常: {e}")
        await db.rollback()
