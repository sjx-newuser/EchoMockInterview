"""
Echo Mock System - WebSocket
========================================
轻薄化路由：所有连接管理和信号响应已经转移至 app.services.ws_manager。
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.ws import WsClientMessage, WsMsgType, WsServerMessage, SystemStatusPayload
from app.services.ws_manager import manager
from app.ai_engine.multimodal.asr import SenseVoiceEngine
from app.ai_engine.llm_provider import llm_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


# =============================================
# WebSocket 路由端点
# =============================================
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await manager.connect(session_id, ws)
    
    import app.services.ws_manager as ws_srv
    if not ws_srv.asr_engine_instance:
        ws_srv.asr_engine_instance = SenseVoiceEngine()

    llm_client.init_app()

    await manager.send(
        session_id,
        WsServerMessage.from_payload(
            session_id=session_id, msg_type=WsMsgType.SYSTEM_STATUS,
            payload=SystemStatusPayload(status="idle", message="环境就绪, 等待面试开始"),
        ),
    )

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = WsClientMessage.model_validate_json(raw)
            except Exception as e:
                logger.error(f"解析 WS 消息失败: {e}")
                continue

            if msg.type == WsMsgType.START_INTERVIEW:
                await manager.handle_start_interview(session_id, msg.parse_payload())
            elif msg.type == WsMsgType.AUDIO_CHUNK:
                await manager.handle_audio_chunk(session_id, msg.parse_payload())
            elif msg.type == WsMsgType.TEXT_MESSAGE:
                await manager.handle_text_message(session_id, msg.parse_payload())
            elif msg.type == WsMsgType.STOP_SPEAKING:
                await manager.handle_stop_speaking(session_id, msg.parse_payload())
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WS 通信异常退出: {e}")
        manager.disconnect(session_id)
