/**
 * Echo Mock System - WebSocket 交互协议定义
 * ==========================================
 * 前后端 WebSocket 全双工通信的唯一类型契约。
 * 后端 Python 侧的 schemas/ws.py 必须与此文件严格对齐。
 */

// =============================================
// 1. 消息类型枚举（前后端共用）
// =============================================

export enum WsMsgType {
  START_INTERVIEW = 'start_interview', // 开始面试
  AUDIO_CHUNK     = 'audio_chunk',     // 发送/接收音频切片
  TEXT_MESSAGE    = 'text_message',    // 发送文字消息
  TEXT_STREAM     = 'text_stream',     // 接收 AI 文本流（打字机效果）
  SYSTEM_STATUS   = 'system_status',   // 接收系统状态（如: AI 正在思考）
  STOP_SPEAKING   = 'stop_speaking',   // 用户主动打断 AI 发言
  ERROR           = 'error',           // 错误信息
}

// =============================================
// 2. 各事件的具体业务载荷（Payload）
// =============================================

/** 开始面试 - 客户端发送 */
export interface StartInterviewPayload {
  target_role: string;
}

/** 音频切片 - 客户端发送 */
export interface AudioChunkPayload {
  seq: number;          // 切片序号，保证音频拼接顺序
  audio_base64: string; // PCM/WAV 音频的 Base64 编码
  is_last: boolean;     // 是否是当前这句话的最后一个切片（VAD 触发）
}

/** 文本消息 - 客户端发送 */
export interface TextMessagePayload {
  text: string;
}

/** 打断 AI 发言 - 客户端发送（无额外业务数据） */
export interface StopSpeakingPayload {
  reason?: string;      // 可选：打断原因（如 "user_click" / "new_speech_detected"）
}

/** AI 文本流 - 服务端推送 */
export interface TextStreamPayload {
  chunk_id: string;     // 属于哪一次 AI 回答的 ID
  seq: number;          // 文本流序号，防止打字机效果乱序
  text: string;         // 增量文本内容
  is_end: boolean;      // 当前回答是否结束
}

/** 系统状态 - 服务端推送 */
export interface SystemStatusPayload {
  status: 'thinking' | 'listening' | 'evaluating' | 'idle'; // AI 当前状态
  message?: string;     // 可选的附加提示信息
}

/** 错误信息 - 服务端推送 */
export interface ErrorPayload {
  code: number;         // 业务错误码
  message: string;      // 人类可读的错误描述
}

// =============================================
// 3. 统一信封格式（Envelope）
// =============================================

/** 信封基础结构 */
interface WsEnvelopeBase {
  id: string;           // 消息唯一 UUID
  timestamp: number;    // 发送时的毫秒级时间戳
  session_id: string;   // 归属的面试场次 ID（信封级别，避免每个 Payload 重复定义）
}

// =============================================
// 4. 判别联合（Discriminated Union）
//    让 TypeScript 根据 type 字段自动推断 payload 类型
// =============================================

/** 客户端 -> 服务端 的所有可能包 */
export type WsClientMessage =
  | (WsEnvelopeBase & { type: WsMsgType.START_INTERVIEW; payload: StartInterviewPayload })
  | (WsEnvelopeBase & { type: WsMsgType.AUDIO_CHUNK;     payload: AudioChunkPayload })
  | (WsEnvelopeBase & { type: WsMsgType.TEXT_MESSAGE;    payload: TextMessagePayload })
  | (WsEnvelopeBase & { type: WsMsgType.STOP_SPEAKING;   payload: StopSpeakingPayload });

/** 服务端 -> 客户端 的所有可能包 */
export type WsServerMessage =
  | (WsEnvelopeBase & { type: WsMsgType.TEXT_STREAM;    payload: TextStreamPayload })
  | (WsEnvelopeBase & { type: WsMsgType.SYSTEM_STATUS;  payload: SystemStatusPayload })
  | (WsEnvelopeBase & { type: WsMsgType.AUDIO_CHUNK;    payload: AudioChunkPayload })
  | (WsEnvelopeBase & { type: WsMsgType.ERROR;          payload: ErrorPayload });
