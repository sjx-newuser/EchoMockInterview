# scripts/init_sensevoice.py
import torch
from funasr import AutoModel

def download_and_init_model():
    print("正在连接 ModelScope 拉取 SenseVoice-Small 权重...")
    print("首次下载大约需要几分钟，请保持网络畅通。")
    
    # 自动检测是否可用 CUDA
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"分配计算设备: {device}")

    try:
        # 这一步会自动下载并缓存模型到 ~/.cache/modelscope/hub/iic/SenseVoiceSmall
        model = AutoModel(
            model="iic/SenseVoiceSmall",
            trust_remote_code=True,
            remote_code="./model.py",
            vad_model="fsmn-vad",
            vad_kwargs={"max_single_segment_time": 30000},
            device=device,
        )
        
        # 强制转换为 FP16，优化显存/内存占用
        model.model.to(torch.float16)
        print("✅ 模型权重下载并加载成功！已配置为 FP16 精度。")
        
    except Exception as e:
        print(f"❌ 模型拉取失败: {e}")

if __name__ == "__main__":
    download_and_init_model()