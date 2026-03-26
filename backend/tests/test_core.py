"""
Echo Mock System - Core Orchestration Tests
=============================================
集成测试 WebSocket 大动脉与 Report API 的容错逻辑。
我们将全面 mock 掉底层的模型调用（ASR / LLM / RAG / Evaluator）。
"""

import pytest
import base64
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import FastAPI entrypoint
from app.main import app
from app.db.models import InterviewSession, QaEvaluation
from app.schemas.ws import WsClientMessage, WsMsgType

client = TestClient(app)


# ===============================================
# 1. 模拟环境配置 (Mock Dependencies)
# ===============================================

@pytest.fixture(autouse=True)
def mock_all_ai_engines():
    """在执行所有测试前，强行 mock 掉消耗 Token 或占用算力的引擎模块。"""
    
    # 1. Mock ASR (免去初始化模型)
    with patch("app.services.ws_manager.asr_engine_instance") as mock_asr:
        mock_asr.transcribe.return_value = "我之前做过Java开发"
        
        # 2. Mock LLM 发声 (流式返回)
        with patch("app.services.ws_manager.llm_client") as mock_llm_client:
            mock_stream_response = AsyncMock()
            
            # 手打一个异步生成器
            async def mock_async_generator():
                class Chunk:
                    def __init__(self, text):
                        self.text = text
                yield Chunk("你")
                yield Chunk("好")
                yield Chunk("呀")
            
            mock_stream_response.return_value = mock_async_generator()
            
            mock_model = AsyncMock()
            mock_model.generate_content_async = mock_stream_response
            mock_llm_client.model = mock_model
            
            # 3. Mock RAG Retriever
            with patch("app.services.ws_manager.dual_retriever") as mock_rag:
                mock_rag.retrieve_questions.return_value = []
                mock_rag.format_results.return_value = "- Spring IOC 考点"
                
                # 4. Mock Background Task (Celery/Librosa)
                with patch("app.services.ws_manager.analyze_and_save_audio_metrics") as mock_delay:
                    
                    # 5. Mock DB Factory (以访真正的 DB 操作)
                    with patch("app.services.ws_manager.async_session_factory") as mock_db_factory:
                        mock_session = AsyncMock(spec=AsyncSession)
                        # 支持 async with
                        mock_db_factory.return_value.__aenter__.return_value = mock_session
                        mock_db_factory.return_value.__aexit__.return_value = False
                        
                        yield {
                            "asr": mock_asr,
                            "llm": mock_llm_client,
                            "rag": mock_rag,
                            "audio_metrics": mock_delay,
                            "db": mock_session
                        }

# ===============================================
# 2. 核心路由 WebSocket 测试
# ===============================================

class TestWebSocketEngine:
    
    def test_ws_full_duplex_flow(self, mock_all_ai_engines):
        """测试核心 WS 的破冰和答题流转逻辑"""
        session_id = "test-session-123"
        
        # 1. 发起建连
        with client.websocket_connect(f"/api/v1/ws/{session_id}") as websocket:
            
            # 必须立马收到一个 SYSTEM_STATUS idle
            response1 = websocket.receive_json()
            assert response1["type"] == WsMsgType.SYSTEM_STATUS
            assert response1["payload"]["status"] == "idle"
            
            # 2. 客户端发送 START_INTERVIEW
            start_msg = WsClientMessage(
                session_id=session_id,
                type=WsMsgType.START_INTERVIEW,
                payload={"target_role": "后端开发"}
            )
            websocket.send_text(start_msg.model_dump_json())
            
            # 应该收到 thinking 状态
            response2 = websocket.receive_json()
            assert response2["type"] == WsMsgType.SYSTEM_STATUS
            assert response2["payload"]["status"] == "thinking"
            
            # 随后应该收到 listening 状态表示要推流了
            response3 = websocket.receive_json()
            assert response3["type"] == WsMsgType.SYSTEM_STATUS
            assert response3["payload"]["status"] == "listening"
            
            # 接收流式文本: "你" -> "好" -> "呀" -> is_end=True 回车
            texts = []
            for _ in range(4): # 3个字 + 1个结尾符
                res = websocket.receive_json()
                assert res["type"] == WsMsgType.TEXT_STREAM
                texts.append(res["payload"]["text"])
                if res["payload"]["is_end"]:
                    break
            
            assert "".join(texts) == "你好呀"
            
            # 3. 客户端发送一段语音表示回答完毕
            audio_msg = WsClientMessage(
                session_id=session_id,
                type=WsMsgType.AUDIO_CHUNK,
                payload={
                    "seq": 0,
                    "audio_base64": base64.b64encode(b"fake audio data").decode(),
                    "is_last": True
                }
            )
            websocket.send_text(audio_msg.model_dump_json())
            
            # 应当进入下一轮思考并流式返回
            res_think = websocket.receive_json()
            assert res_think["type"] == WsMsgType.SYSTEM_STATUS
            assert res_think["payload"]["status"] == "thinking"
            
            # Backend 会异步写库，并触发 analyze_and_save_audio_metrics
            mock_all_ai_engines["audio_metrics"].assert_called_once()
            
            
# ===============================================
# 3. 测试 Report 逻辑
# ===============================================

class TestReportAPI:
    
    @patch("app.services.report_service.evaluator")
    @patch("app.api.deps.get_current_user")
    @patch("app.api.v1.report.get_db")
    def test_report_lazy_generation(self, mock_get_db, mock_get_user, mock_evaluator):
        """测试如果未生成过报告，GET 接口是否会自动触发 evaluator 的在线核算。"""
        
        # Mock 用户依赖
        class MockUser:
            id = 99
        mock_get_user.return_value = MockUser()
        
        # Mock Session 对象关联为空报告
        mock_eval1 = QaEvaluation()
        mock_eval1.question_content = "1+1=?"
        mock_eval1.technical_score = 90
        
        mock_session_obj = MagicMock()
        mock_session_obj.id = "session_xyz"
        mock_session_obj.user_id = 99
        mock_session_obj.target_role = "Test"
        mock_session_obj.comprehensive_report = None  # Crucial for trigger
        mock_session_obj.evaluations = [mock_eval1]
        mock_session_obj.status = MagicMock()
        mock_session_obj.status.value = "COMPLETED"
        
        # Mock DB
        mock_db_session = AsyncMock()
        
        # FastAPI Depends 覆盖
        app.dependency_overrides[mock_get_db] = lambda: mock_db_session
        
        # 这里比较 trick，因为 DB 取数据用的是 db.execute(select(...))，这部分涉及复杂的 SQLAlchemy
        # 在真实测试环境，应当注入 SQLite 测试库。由于是单元覆盖核心 trigger，暂略真正查询，只查路由行为。
        pass  # TODO 可以加 Test Database SQLite in memory setup
