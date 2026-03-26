"""
Echo Mock System - WebSocket 交互协议定义 (后端侧)
====================================================
前端 TypeScript 侧的 types/websocket.ts 必须与此文件严格对齐。
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# =============================================
# 1. 消息类型枚举（与前端 WsMsgType 严格对应）
# =============================================

class WsMsgType(str, Enum):
    START_INTERVIEW = "start_interview"
    AUDIO_CHUNK     = "audio_chunk"
    TEXT_MESSAGE    = "text_message"
    TEXT_STREAM     = "text_stream"
    SYSTEM_STATUS   = "system_status"
    STOP_SPEAKING   = "stop_speaking"
    ERROR           = "error"


# =============================================
# 2. 进站载荷（客户端 -> 服务端）
# =============================================

class StartInterviewPayload(BaseModel):
    target_role: str = Field(..., description="目标岗位（如 Java 后端、前端）")


class AudioChunkPayload(BaseModel):
    seq: int = Field(..., description="音频切片序号，用于防乱序")
    audio_base64: str = Field(..., description="Base64 编码的音频数据")
    is_last: bool = Field(default=False, description="是否为该段发言的结束（VAD 触发）")


class StopSpeakingPayload(BaseModel):
    reason: Optional[str] = Field(default=None, description="打断原因（如 user_click / new_speech_detected）")


class TextMessagePayload(BaseModel):
    text: str = Field(..., description="用户发送的文本消息内容")


# =============================================
# 3. 出站载荷（服务端 -> 客户端）
# =============================================

class TextStreamPayload(BaseModel):
    chunk_id: str = Field(..., description="属于哪一次 AI 回答的 ID")
    seq: int = Field(..., description="文本流序号，防止打字机效果乱序")
    text: str = Field(..., description="增量文本内容")
    is_end: bool = Field(default=False, description="当前回答是否结束")


class SystemStatusPayload(BaseModel):
    status: str = Field(..., description="AI 当前状态：thinking / listening / evaluating / idle")
    message: Optional[str] = Field(default=None, description="可选的附加提示信息")


class ErrorPayload(BaseModel):
    code: int = Field(..., description="业务错误码")
    message: str = Field(..., description="人类可读的错误描述")


# =============================================
# 4. 统一信封格式（Envelope）
# =============================================

class WsClientMessage(BaseModel):
    """客户端 -> 服务端 的统一信封。"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    session_id: str = Field(..., description="归属的面试场次 ID")
    type: WsMsgType
    payload: Dict[str, Any] = Field(..., description="具体业务数据，根据 type 再解析为对应 Payload")

    def parse_payload(self) -> BaseModel:
        """根据 type 将 payload 字典解析为强类型的 Pydantic 模型。"""
        _map = {
            WsMsgType.START_INTERVIEW: StartInterviewPayload,
            WsMsgType.AUDIO_CHUNK:     AudioChunkPayload,
            WsMsgType.TEXT_MESSAGE:    TextMessagePayload,
            WsMsgType.STOP_SPEAKING:   StopSpeakingPayload,
        }
        model_cls = _map.get(self.type)
        if model_cls is None:
            raise ValueError(f"未知的客户端消息类型: {self.type}")
        return model_cls(**self.payload)


class WsServerMessage(BaseModel):
    """服务端 -> 客户端 的统一信封。"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    session_id: str = Field(..., description="归属的面试场次 ID")
    type: WsMsgType
    payload: Dict[str, Any] = Field(..., description="具体业务数据")

    @classmethod
    def from_payload(cls, session_id: str, msg_type: WsMsgType, payload: BaseModel) -> "WsServerMessage":
        """快捷工厂方法：从强类型 Payload 构建完整信封。"""
        return cls(
            session_id=session_id,
            type=msg_type,
            payload=payload.model_dump(),
        )
