"""
Echo Mock System - 全链路 E2E 集成测试脚本
=============================================
这个脚本不针对“某个模块的函数”，而是站在“前端客户端”的视角，
按照一个真实用户的生命周期，完整贯穿调用整个后端 API 系统：

生命周期：
1. [API] 注册测试账号
2. [API] 登录账号，获取 JWT Token
3. [API] 带着 Token 发起一场 "后端开发" 面试，得到 session_id
4. [WS]  建立 WebSocket 连接
5. [WS]  发送 START_INTERVIEW
6. [WS]  接收 AI 思考与流式破冰文本
7. [WS]  发送 模拟候选用人说话的 AUDIO_CHUNK
8. [WS]  接收 AI 下一步的推流
9. [WS]  主动断开连接
10. [API] 查询历史记录，应该包含刚刚的一通对话
11. [API] 请求生成并获取综合面试报告能力
"""

import sys
import os
import base64
import time
from fastapi.testclient import TestClient

# 添加后端目录到 sys.path 以便直接运行
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.schemas.ws import WsClientMessage, WsMsgType

client = TestClient(app)

def run_comprehensive_e2e():
    print("\n" + "="*50)
    print("🚀 开始执行全链路后端集成测试 (E2E Test)")
    print("="*50 + "\n")

    # ---------------------------------------------------------
    # 1. 用户注册与登录
    # ---------------------------------------------------------
    print("⏳ [1/6] 正在测试用户注册与登录...")
    test_user = {"username": f"e2e_user_{int(time.time())}", "password": "password123"}
    
    # 注册
    res_reg = client.post("/api/v1/auth/register", json=test_user)
    if res_reg.status_code == 201:
        print("  ✅ 注册成功")
    elif res_reg.status_code == 400 and "already registered" in res_reg.text:
         print("  ✅ 用户已存在，直接测试登录")
    else:
        print(f"  ❌ 注册失败: {res_reg.text}")
        sys.exit(1)

    # 登录获取 Token
    res_login = client.post(
        "/api/v1/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]}
    )
    if res_login.status_code != 200:
        print(f"  ❌ 登录失败: {res_login.text}")
        sys.exit(1)
    
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  ✅ 登录成功，成功获取 JWT Token")


    # ---------------------------------------------------------
    # 2. 创建面试场次
    # ---------------------------------------------------------
    print("\n⏳ [2/6] 正在测试创建面试场次...")
    res_create = client.post(
        "/api/v1/interviews/",
        json={"target_role": "测试工程师"},
        headers=headers
    )
    if res_create.status_code != 201:
        print(f"  ❌ 创建面试失败: {res_create.text}")
        sys.exit(1)
    
    session_id = res_create.json()["id"]
    print(f"  ✅ 成功创建面试场次，分配 Session ID: {session_id}")


    # ---------------------------------------------------------
    # 3. WebSocket 全双工长链接对答 (Mock 底层 AI 防损耗)
    # ---------------------------------------------------------
    print("\n⏳ [3/6] 开始建立 WebSocket 兵棋推演...")
    
    # 我们打入 mock，防止本地跑 E2E 真的去疯狂调 OpenAI 扣钱
    from unittest.mock import patch, AsyncMock
    with patch("app.services.ws_manager.asr_engine_instance") as mock_asr, \
         patch("app.services.ws_manager.llm_client") as mock_llm_client, \
         patch("app.services.ws_manager.dual_retriever") as mock_rag, \
         patch("app.services.ws_manager.analyze_and_save_audio_metrics") as mock_audio_metrics:
        
        # 配装强力推进器
        mock_asr.transcribe.return_value = "这是我第一次测试这个全系统"
        
        async def mock_async_generator():
            class Chunk:
                def __init__(self, text):
                    self.text = text
            yield Chunk("非常好，")
            yield Chunk("接下来请回答")
            yield Chunk("什么是边界值分析？")
            
        mock_model = AsyncMock()
        mock_model.generate_content_async.return_value = mock_async_generator()
        mock_llm_client.model = mock_model
        
        mock_rag.retrieve_questions.return_value = []
        mock_rag.format_results.return_value = "- 解释一下边界值"

        # 连接建立！注意，因为 FastAPI TestClient 的 ws 建立没有 auth header，实际会在连接建立后才验证业务安全（如果业务做了验证）。
        # 此处我们的 ws 端点为了简化测试只接收 session_id。
        with client.websocket_connect(f"/api/v1/ws/{session_id}") as websocket:
            
            # (1) 检查系统就绪
            ws_res = websocket.receive_json()
            assert ws_res["payload"]["status"] == "idle"
            print("  ✅ WebSocket 握手成功，状态就绪")
            
            # (2) 发起 START
            start_msg = WsClientMessage(
                session_id=session_id,
                type=WsMsgType.START_INTERVIEW,
                payload={"target_role": "测试工程师"}
            )
            websocket.send_text(start_msg.model_dump_json())
            
            print("  ✅ 已发送 START_INTERVIEW, 等待 AI 响应流...")
            
            # 过滤前面的 thinking 等状态，拦截文本流
            full_ai_response = ""
            while True:
                resp = websocket.receive_json()
                if resp["type"] == WsMsgType.TEXT_STREAM:
                    full_ai_response += resp["payload"]["text"]
                    if resp["payload"]["is_end"]:
                        break
            
            print(f"  🤖 AI 破冰发问: {full_ai_response}")
            
            # (3) 用户发送模拟音频
            fake_audio = base64.b64encode(b"010101").decode("utf-8")
            audio_msg = WsClientMessage(
                session_id=session_id,
                type=WsMsgType.AUDIO_CHUNK,
                payload={
                    "seq": 0,
                    "audio_base64": fake_audio,
                    "is_last": True
                }
            )
            websocket.send_text(audio_msg.model_dump_json())
            print("  ✅ 已发送 AUDIO_CHUNK 模拟用户说话结束")
            
            # 接收第二轮 AI 对话
            full_ai_response_2 = ""
            while True:
                resp = websocket.receive_json()
                if resp["type"] == WsMsgType.TEXT_STREAM:
                    full_ai_response_2 += resp["payload"]["text"]
                    if resp["payload"]["is_end"]:
                        break
                        
            print(f"  🤖 AI 聆听后下一轮追问: {full_ai_response_2}")
            print("  ✅ WebSocket 智能状态机运转健康！")
            
    # 此刻出了 with block，WebSocket 会自动客户端 disconnect。

    # ---------------------------------------------------------
    # 4. 获取历史对答记录
    # ---------------------------------------------------------
    print("\n⏳ [4/6] 正在拉取该场次详情与历史记录...")
    res_detail = client.get(f"/api/v1/interviews/{session_id}", headers=headers)
    if res_detail.status_code != 200:
        print(f"  ❌ 拉取详情失败: {res_detail.text}")
        sys.exit(1)
        
    print(f"  ✅ 拉取成功，状态：{res_detail.json()['status']}")
    
    # ---------------------------------------------------------
    # 5. 触发并获取深度评估报告
    # ---------------------------------------------------------
    print("\n⏳ [5/6] 正在触发生成并拉取综合评估报告...")
    
    # 同样为了保护你的大模型代币，这里 patch 掉 evaluator 引发报告生成的底层动作
    with patch("app.services.report_service.evaluator") as mock_evaluator:
        
        async def mock_gen_report(*args, **kwargs):
            return {
                "overall_score": 88.5,
                "dimension_scores": [
                    {"name": "Technical", "score": 90},
                    {"name": "Communication", "score": 85}
                ],
                "report_markdown": "## E2E 测试模拟的一份极其优秀的报告"
            }
        mock_evaluator.generate_comprehensive_report.side_effect = mock_gen_report
        
        res_report = client.get(f"/api/v1/reports/{session_id}", headers=headers)
        if res_report.status_code != 200:
            print(f"  ❌ 生成报告失败: {res_report.text}")
            sys.exit(1)
            
        rep_json = res_report.json()
        print(f"  ✅ 报告已就绪!")
        print(f"     -> 总得分: {rep_json['overall_score']}")
        print(f"     -> 维度评价: {rep_json['dimension_scores']}")
        print(f"     -> 报告缩略图: {rep_json['comprehensive_report'][:20]}...")

    print("\n" + "="*50)
    print("🎉 E2E 大捷！后端系统所有核心主线剧情从头贯穿到尾，没有断裂！")
    print("="*50 + "\n")


if __name__ == "__main__":
    run_comprehensive_e2e()
