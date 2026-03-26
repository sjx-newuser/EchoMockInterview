"""
Echo Mock System - 多模态模块单元测试
=======================================
覆盖: asr.py / express.py / async_tasks.py
所有外部依赖均通过 mock 隔离，无需 GPU / 模型 / 数据库。
"""

import io
import pytest
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================
# 辅助函数：生成内存中的 WAV 字节流
# =============================================

def _make_wav_bytes(duration_sec=1.0, sr=16000, channels=1, freq=440.0):
    """生成一段正弦波 WAV 字节流，用于测试。"""
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False, dtype=np.float32)
    if channels == 1:
        data = 0.5 * np.sin(2 * np.pi * freq * t)
    else:
        mono = 0.5 * np.sin(2 * np.pi * freq * t)
        data = np.column_stack([mono] * channels)  # shape: (samples, channels)

    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV", subtype="FLOAT")
    return buf.getvalue()


def _make_silent_wav_bytes(duration_sec=1.0, sr=16000):
    """生成一段静音 WAV 字节流。"""
    data = np.zeros(int(sr * duration_sec), dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV", subtype="FLOAT")
    return buf.getvalue()


def _make_empty_wav_bytes(sr=16000):
    """生成零长度 WAV 字节流。"""
    data = np.array([], dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV", subtype="FLOAT")
    return buf.getvalue()


# =============================================
# 1. asr.py 测试
# =============================================

class TestSenseVoiceEngine:
    """测试 ASR 核心引擎 (SenseVoiceEngine)"""

    def _make_engine(self):
        """创建一个未加载模型的引擎实例。"""
        # 避免使用全局单例，以便每个测试独立
        from app.ai_engine.multimodal.asr import SenseVoiceEngine
        return SenseVoiceEngine()

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_load_model_success(self, mock_auto_model):
        """模型正常加载后 _is_ready 应为 True"""
        engine = self._make_engine()
        engine.load_model()

        assert engine._is_ready is True
        mock_auto_model.assert_called_once()

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_load_model_only_once(self, mock_auto_model):
        """重复调用 load_model 不应重新加载"""
        engine = self._make_engine()
        engine.load_model()
        engine.load_model()  # 第二次

        assert mock_auto_model.call_count == 1

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_load_model_failure_raises(self, mock_auto_model):
        """模型加载失败应抛出异常，_is_ready 保持 False"""
        mock_auto_model.side_effect = RuntimeError("CUDA OOM")
        engine = self._make_engine()

        with pytest.raises(RuntimeError, match="CUDA OOM"):
            engine.load_model()

        assert engine._is_ready is False

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_transcribe_success(self, mock_auto_model):
        """正常转写：返回模型输出的文本"""
        mock_model_instance = MagicMock()
        mock_model_instance.generate.return_value = [{"text": "你好世界"}]
        mock_auto_model.return_value = mock_model_instance

        engine = self._make_engine()
        wav_bytes = _make_wav_bytes()
        result = engine.transcribe(wav_bytes)

        assert result == "你好世界"
        mock_model_instance.generate.assert_called_once()

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_transcribe_auto_loads_model(self, mock_auto_model):
        """transcribe 时若模型未加载，应自动触发 load_model"""
        mock_model_instance = MagicMock()
        mock_model_instance.generate.return_value = [{"text": "自动加载"}]
        mock_auto_model.return_value = mock_model_instance

        engine = self._make_engine()
        assert engine._is_ready is False

        engine.transcribe(_make_wav_bytes())

        assert engine._is_ready is True

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_transcribe_empty_result(self, mock_auto_model):
        """模型返回空列表时应返回空字符串"""
        mock_model_instance = MagicMock()
        mock_model_instance.generate.return_value = []
        mock_auto_model.return_value = mock_model_instance

        engine = self._make_engine()
        result = engine.transcribe(_make_wav_bytes())

        assert result == ""

    @patch("app.ai_engine.multimodal.asr.AutoModel")
    def test_transcribe_returns_empty_on_error(self, mock_auto_model):
        """推理过程异常应返回空字符串而非抛出"""
        mock_model_instance = MagicMock()
        mock_model_instance.generate.side_effect = RuntimeError("inference error")
        mock_auto_model.return_value = mock_model_instance

        engine = self._make_engine()
        result = engine.transcribe(_make_wav_bytes())

        assert result == ""


# =============================================
# 2. express.py 测试
# =============================================

class TestAnalyzeAudioExpression:
    """测试旁路语音特征分析 (analyze_audio_expression)"""

    def test_normal_audio(self):
        """正常音频应返回包含四个 key 的字典，值为数值类型"""
        from app.ai_engine.multimodal.express import analyze_audio_expression

        wav_bytes = _make_wav_bytes(duration_sec=2.0)
        result = analyze_audio_expression(wav_bytes, "这是一段测试文本用于验证语速计算")

        assert isinstance(result, dict)
        for key in ("wpm", "pitch_var", "rms_var", "pause_ratio"):
            assert key in result, f"缺少字段: {key}"
            assert isinstance(result[key], float), f"{key} 应为 float"

        # wpm 应为正值（有文本有时长）
        assert result["wpm"] > 0
        # pause_ratio 应在 [0, 1]
        assert 0.0 <= result["pause_ratio"] <= 1.0

    def test_empty_audio_returns_zeros(self):
        """空音频应返回全零的防御性结果"""
        from app.ai_engine.multimodal.express import analyze_audio_expression

        wav_bytes = _make_empty_wav_bytes()
        result = analyze_audio_expression(wav_bytes, "无所谓")

        assert result == {"wpm": 0.0, "pitch_var": 0.0, "rms_var": 0.0, "pause_ratio": 0.0}

    def test_stereo_audio_handled(self):
        """双声道音频应自动转为单声道处理，不报错"""
        from app.ai_engine.multimodal.express import analyze_audio_expression

        wav_bytes = _make_wav_bytes(duration_sec=1.0, channels=2)
        result = analyze_audio_expression(wav_bytes, "双声道测试")

        assert isinstance(result, dict)
        assert "wpm" in result

    def test_empty_text_wpm_zero(self):
        """空文本时 wpm 应为 0"""
        from app.ai_engine.multimodal.express import analyze_audio_expression

        wav_bytes = _make_wav_bytes(duration_sec=1.0)
        result = analyze_audio_expression(wav_bytes, "")

        assert result["wpm"] == 0.0

    def test_returns_default_on_invalid_input(self):
        """传入非法字节流应返回全零兜底"""
        from app.ai_engine.multimodal.express import analyze_audio_expression

        result = analyze_audio_expression(b"not-a-wav-file", "测试")

        assert result == {"wpm": 0.0, "pitch_var": 0.0, "rms_var": 0.0, "pause_ratio": 0.0}

    def test_silent_audio_pause_ratio(self):
        """纯数字静音（全零）在 librosa 相对 dB 阈值下 pause_ratio 为 0.0；
        而近静音（含微弱噪声）应有较高 pause_ratio。"""
        from app.ai_engine.multimodal.express import analyze_audio_expression

        # 全零静音: librosa.effects.split 使用相对阈值，无法分割
        wav_bytes = _make_silent_wav_bytes(duration_sec=2.0)
        result = analyze_audio_expression(wav_bytes, "静音")
        assert result["pause_ratio"] == 0.0  # 已知行为

        # 短脉冲 + 长静音：应有明显 pause_ratio
        sr = 16000
        duration = 2.0
        samples = int(sr * duration)
        data = np.zeros(samples, dtype=np.float32)
        # 在开头加入一小段脉冲
        data[:800] = 0.5 * np.sin(2 * np.pi * 440 * np.arange(800) / sr).astype(np.float32)
        buf = io.BytesIO()
        sf.write(buf, data, sr, format="WAV", subtype="FLOAT")
        mixed_bytes = buf.getvalue()

        result2 = analyze_audio_expression(mixed_bytes, "短脉冲")
        assert result2["pause_ratio"] > 0.3  # 大部分是静音


# =============================================
# 3. async_tasks.py 测试
# =============================================

class TestAnalyzeAndSaveAudioMetrics:
    """测试异步后台分析任务 (analyze_and_save_audio_metrics)"""

    @pytest.mark.asyncio
    @patch("app.ai_engine.multimodal.async_tasks.analyze_audio_expression")
    async def test_success_flow(self, mock_analyze):
        """正常流程：提取特征 → 查询 DB → 更新字段 → commit"""
        from app.ai_engine.multimodal.async_tasks import analyze_and_save_audio_metrics
        from app.db.models import AudioAnalysisStatus

        mock_analyze.return_value = {
            "wpm": 120.5, "pitch_var": 0.03, "rms_var": 0.0001, "pause_ratio": 0.15
        }

        mock_eval = MagicMock()
        mock_db = AsyncMock()
        mock_db.get.return_value = mock_eval

        await analyze_and_save_audio_metrics(mock_db, "eval-123", b"audio", "你好")

        mock_analyze.assert_called_once_with(b"audio", "你好")
        mock_db.get.assert_awaited_once()
        assert mock_eval.speech_rate == 120.5
        assert mock_eval.pause_ratio == 0.15
        assert mock_eval.audio_analysis_status == AudioAnalysisStatus.COMPLETED
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skip_on_empty_eval_id(self):
        """eval_id 为空时直接跳过，不调用任何 DB 操作"""
        from app.ai_engine.multimodal.async_tasks import analyze_and_save_audio_metrics

        mock_db = AsyncMock()

        await analyze_and_save_audio_metrics(mock_db, "", b"audio", "你好")

        mock_db.get.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.ai_engine.multimodal.async_tasks.analyze_audio_expression")
    async def test_db_record_not_found(self, mock_analyze):
        """找不到对应评估记录时，应只打日志不报错"""
        from app.ai_engine.multimodal.async_tasks import analyze_and_save_audio_metrics

        mock_analyze.return_value = {
            "wpm": 100.0, "pitch_var": 0.01, "rms_var": 0.0, "pause_ratio": 0.1
        }

        mock_db = AsyncMock()
        mock_db.get.return_value = None  # 记录不存在

        # 不应抛出异常
        await analyze_and_save_audio_metrics(mock_db, "missing-id", b"audio", "你好")

        mock_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.ai_engine.multimodal.async_tasks.analyze_audio_expression")
    async def test_exception_triggers_rollback(self, mock_analyze):
        """analyze_audio_expression 抛出异常时应触发 db.rollback()"""
        from app.ai_engine.multimodal.async_tasks import analyze_and_save_audio_metrics

        mock_analyze.side_effect = RuntimeError("librosa boom")

        mock_db = AsyncMock()

        await analyze_and_save_audio_metrics(mock_db, "eval-456", b"audio", "你好")

        mock_db.rollback.assert_awaited_once()
        mock_db.commit.assert_not_awaited()
