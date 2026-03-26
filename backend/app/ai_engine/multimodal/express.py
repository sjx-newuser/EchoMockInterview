"""
Echo Mock System - 旁路语音特征分析
====================================
使用 Librosa 提取声学特征硬核指标（不参与对话关键链路，仅后台处理落库）
"""

import io
import logging
import numpy as np
import soundfile as sf
import librosa

logger = logging.getLogger(__name__)

def analyze_audio_expression(pcm_bytes: bytes, asr_text: str) -> dict:
    """
    提取硬核的量化声学特征
    返回: wpm(语速), pitch_var(音高方差), rms_var(能量方差), pause_ratio(静音比例)
    """
    try:
        with io.BytesIO(pcm_bytes) as f:
            y, sr = sf.read(f, dtype='float32')

        if len(y.shape) > 1:
            y = y.mean(axis=1)

        # 防御性保护：处理空音频
        if len(y) == 0:
            return {"wpm": 0.0, "pitch_var": 0.0, "rms_var": 0.0, "pause_ratio": 0.0}

        # 1. 语速 (Words Per Minute)
        duration_sec = len(y) / sr
        text_length = len(asr_text.replace(" ", "").replace("，", "").replace("。", ""))
        wpm = (text_length / duration_sec) * 60 if duration_sec > 0 else 0.0

        # 2. 情绪稳定性 - RMS 能量方差抖动
        rms = librosa.feature.rms(y=y)[0]
        rms_var = float(np.var(rms))

        # 3. 情绪稳定性 - Pitch 音高方差抖动
        f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr)
        f0_valid = f0[~np.isnan(f0)]
        pitch_var = float(np.var(f0_valid)) if len(f0_valid) > 0 else 0.0

        # 4. 流利度 - 提取发声段和静音段比例
        non_mute_intervals = librosa.effects.split(y, top_db=30)
        active_samples = sum([end - start for start, end in non_mute_intervals])
        fluency_ratio = active_samples / len(y)
        pause_ratio = max(0.0, 1.0 - fluency_ratio)

        logger.info(f"[旁路特征提取完成] WPM: {wpm:.1f}, Pitch_Var: {pitch_var:.2f}, RMS_Var: {rms_var:.4f}, Pause: {pause_ratio:.2%}")
        return {
            "wpm": round(wpm, 2),
            "pitch_var": round(pitch_var, 4),
            "rms_var": round(rms_var, 6),
            "pause_ratio": round(pause_ratio, 4)
        }

    except Exception as e:
        logger.error(f"[Librosa 分析失败]: {e}")
        return {"wpm": 0.0, "pitch_var": 0.0, "rms_var": 0.0, "pause_ratio": 0.0}
