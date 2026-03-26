"""
Echo Mock System - 本地语音识别独立测试
========================================
测试 `backend/app/ai_engine/multimodal/asr.py` 中的 SenseVoiceEngine。
将读取 ModelScope 下载时的自带示例音频进行极速转写。
"""

import sys
import os
import time

# 将 backend 目录加入 Python 搜索路径，以便能 import app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ai_engine.multimodal.asr import asr_engine

def main():
    print("=" * 60)
    print(" 🎤  Echo Mock System - 离线 ASR 极速测试")
    print("=" * 60)

    # 寻找 ModelScope 缓存里的测试音频 (这段录音说的是: "今天是2022年4月11号...")
    # Modelscope 默认把它下到了这个路径
    home_dir = os.path.expanduser("~")
    test_audio_path = os.path.join(
        home_dir,
        ".cache/modelscope/hub/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/example/vad_example.wav"
    )

    if not os.path.exists(test_audio_path):
        print(f"❌ 找不到测试音频文件: {test_audio_path}")
        print("请确认已经执行过了 python scripts/init_sensevoice.py")
        sys.exit(1)

    print(f"[1/3] 正在挂载 SenseVoice 模型到显存 (只在初次拉起时耗时)...\n")
    start_time = time.time()
    asr_engine.load_model()
    load_time = time.time() - start_time
    print(f"\n✅ 模型加载完成，耗时: {load_time:.2f} 秒\n")

    print(f"[2/3] 正在读取音频字节流 (模拟前端 WebSocket 传过来的二进制)...\n")
    with open(test_audio_path, "rb") as f:
        audio_bytes = f.read()
    print(f"✅ 读取成功，总计 {len(audio_bytes) / 1024:.2f} KB\n")

    print(f"[3/3] 正在将音频字节流进行本地推理识别...\n")
    start_time = time.time()
    transcription = asr_engine.transcribe(audio_bytes)
    transcription_time = time.time() - start_time

    print("-" * 60)
    print("✨ 最终识别结果:")
    print(f"\n>> 「{transcription}」\n")
    print("-" * 60)
    print(f"✅ 推理耗时: {transcription_time:.3f} 秒")
    print("=" * 60)


if __name__ == "__main__":
    main()
