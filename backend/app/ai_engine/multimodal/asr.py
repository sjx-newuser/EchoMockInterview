"""
Echo Mock System - 实时语音识别 (ASR)
=====================================
基于 FunASR 与 ModelScope 的 SenseVoiceSmall 本地端侧模型，
提供高精度的极速离线音频转写能力。
"""

import logging
import torch
from funasr import AutoModel
import io
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

class SenseVoiceEngine:
    """ASR 核心引擎（单例模式，随服务启动加载进显存）"""

    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = None
        self._is_ready = False

    def load_model(self):
        """延迟加载模型，防止影响应用启动时间"""
        if self._is_ready:
            return

        logger.info(f"[ASR] 正在初始化 SenseVoiceSmall (Device: {self.device})")
        try:
            self.model = AutoModel(
                model="iic/SenseVoiceSmall",
                trust_remote_code=True,
                vad_model="fsmn-vad",
                vad_kwargs={"max_single_segment_time": 30000},
                device=self.device,
            )
            
            self._is_ready = True
            logger.info("[ASR] 语音模型加载成功，状态: 就绪")
        except Exception as e:
            logger.error(f"[ASR] 语音模型加载失败: {e}")
            raise

    def transcribe(self, pcm_bytes: bytes) -> str:
        """
        将字节流（PCM/WAV）转换为 NumPy 数组并进行推理。
        """
        if not self._is_ready:
            self.load_model()
            
        try:
            # 读取音频字节数组
            with io.BytesIO(pcm_bytes) as f:
                data, samplerate = sf.read(f, dtype='float32')

            # FunASR Inference
            # res 是一个列表，提取字典中的 "text" 或 "text_postprocessed"
            res = self.model.generate(
                input=data,
                cache={},
                language="zh",
                use_itn=True,
                batch_size_s=60,
            )
            
            if not res:
                return ""
            
            text = res[0].get("text", "")
            return text
            
        except Exception as e:
            logger.error(f"[ASR] 转写失败: {e}")
            return ""

# 全局单例
asr_engine = SenseVoiceEngine()
