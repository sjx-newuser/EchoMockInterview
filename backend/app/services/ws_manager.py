"""
Echo Mock System - WebSocket 核心引擎业务级封装
===============================================
所有的 `app/api/v1/ws.py` 内繁重的逻辑和 Context，全部转移致此。
使得路由层保持纯净的转发功能。
"""

import base64
import logging
import asyncio
import subprocess
import tempfile
import os
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

# schemas
from app.schemas.ws import (
    AudioChunkPayload,
    StartInterviewPayload,
    StopSpeakingPayload,
    SystemStatusPayload,
    TextMessagePayload,
    TextStreamPayload,
    WsClientMessage,
    WsMsgType,
    WsServerMessage,
)
from app.db.database import async_session_factory
from app.db.models import DialogueMessage, QaEvaluation

# ai engine
from app.ai_engine.multimodal.asr import SenseVoiceEngine
from app.ai_engine.multimodal.async_tasks import analyze_and_save_audio_metrics
from app.ai_engine.agent.state_machine import InterviewStateMachine
from app.ai_engine.agent.memory import MemoryManager
from app.ai_engine.rag.dual_retriever import dual_retriever
from app.ai_engine.evaluator import evaluator
from app.ai_engine.llm_provider import llm_client

logger = logging.getLogger(__name__)

# Lazy load ASR engine (单例模式)
asr_engine_instance = None


class InterviewSessionContext:
    """包装单个活跃 WebSocket 的 AI 内存树和流控开关。"""
    def __init__(self, target_role: str):
        self.target_role = target_role
        self.state_machine = InterviewStateMachine(target_role)
        self.memory = MemoryManager()
        self.history = []
        
        self.current_round = 0
        self.current_question = ""   
        
        self.audio_buffer: list[bytes] = []
        self.cancel_event = asyncio.Event()

    def add_memory(self, speaker: str, content: str):
        self.history.append({"speaker": speaker, "content": content, "round_seq": self.current_round})

def _convert_to_wav(webm_bytes: bytes) -> bytes:
    """Invokes ffmpeg to transcode browser WebM/Opus -> 16kHz mono WAV."""
    if not webm_bytes or len(webm_bytes) < 10:
        return b""
        
    f_in_name = ""
    f_out_name = ""
    try:
        # 使用临时文件代替 pipe:0 管道，解决 WebM (Matroska) 解码器在获取 stream 时无法 Seek 导致的 EBML 头部解析失败
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f_in:
            f_in.write(webm_bytes)
            f_in_name = f_in.name
            
        f_out_name = f_in_name + ".wav"
        
        command = [
            "ffmpeg", "-y", "-i", f_in_name,
            "-f", "wav", "-ac", "1", "-ar", "16000", f_out_name
        ]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr_data = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFmpeg 转码失败, returncode={process.returncode}, stderr:\n{stderr_data.decode('utf-8', errors='replace')}")
            wav_data = b""  # 返回空，让外层优雅告警而不是传错格式给 soundfile
        else:
            with open(f_out_name, "rb") as f:
                wav_data = f.read()
                
        return wav_data
    except Exception as e:
        logger.error(f"FFmpeg 调用异常: {e}")
        return b""
    finally:
        # 清理临时文件
        if f_in_name and os.path.exists(f_in_name):
            try: os.remove(f_in_name)
            except: pass
        if f_out_name and os.path.exists(f_out_name):
            try: os.remove(f_out_name)
            except: pass


class ConnectionManager:
    """负责所有面试连接的核心业务管理类。"""
    def __init__(self):
        self._active: dict[str, WebSocket] = {}
        self._contexts: dict[str, InterviewSessionContext] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._active[session_id] = ws
        logger.info(f"[WS Service] 连接建立: session={session_id}")

    def disconnect(self, session_id: str):
        self._active.pop(session_id, None)
        self._contexts.pop(session_id, None)
        logger.info(f"[WS Service] 连接断开: session={session_id}")

    async def send(self, session_id: str, message: WsServerMessage):
        ws = self._active.get(session_id)
        if ws:
            try:
                await ws.send_text(message.model_dump_json())
            except RuntimeError:
                pass

    def init_context(self, session_id: str, target_role: str):
        self._contexts[session_id] = InterviewSessionContext(target_role)

    def get_context(self, session_id: str) -> Optional[InterviewSessionContext]:
        return self._contexts.get(session_id)

    async def handle_start_interview(self, session_id: str, payload: StartInterviewPayload):
        self.init_context(session_id, payload.target_role)
        ctx = self.get_context(session_id)
        
        await self.send(
            session_id,
            WsServerMessage.from_payload(
                session_id=session_id, msg_type=WsMsgType.SYSTEM_STATUS,
                payload=SystemStatusPayload(status="thinking", message="AI 设计开场白..."),
            )
        )
        
        stage, sys_prompt = ctx.state_machine.get_stage_prompt(ctx.current_round)
        await self._stream_llm_response(session_id, ctx, sys_prompt)


    async def handle_audio_chunk(self, session_id: str, payload: AudioChunkPayload):
        ctx = self.get_context(session_id)
        if not ctx:
            return

        audio_bytes = base64.b64decode(payload.audio_base64)
        ctx.audio_buffer.append(audio_bytes)

        if not payload.is_last:
            return

        await self.send(
            session_id,
            WsServerMessage.from_payload(
                session_id=session_id, msg_type=WsMsgType.SYSTEM_STATUS,
                payload=SystemStatusPayload(status="thinking", message="解析语音并生成回复..."),
            )
        )

        full_audio_webm = b"".join(ctx.audio_buffer)
        ctx.audio_buffer.clear() 
        
        # 核心转换：将 WebM (由前端 MediaRecorder 生成) 转换为 PCM/WAV 
        full_audio = _convert_to_wav(full_audio_webm)
        
        if not full_audio:
            logger.warning("[WS Service] 收到空音频或无效音频数据，跳过分析")
            await self.send(
                session_id,
                WsServerMessage.from_payload(
                    session_id=session_id, msg_type=WsMsgType.SYSTEM_STATUS,
                    payload=SystemStatusPayload(status="listening", message="未检测到声音，请重试"),
                )
            )
            return
            
        global asr_engine_instance
        if not asr_engine_instance:
             asr_engine_instance = SenseVoiceEngine()
             
        user_text = asr_engine_instance.transcribe(full_audio)
        if not user_text.strip():
            user_text = "（候选人似乎没说话）"
        
        ctx.add_memory("USER", user_text)

        # ---- 持久化 USER 消息到数据库 ----
        async with async_session_factory() as db:
            db.add(DialogueMessage(
                session_id=session_id,
                round_seq=ctx.current_round,
                speaker="USER",
                content=user_text,
            ))
            await db.commit()

        async with async_session_factory() as db:
            new_qa = QaEvaluation(
                session_id=session_id,
                question_content=ctx.current_question,
                user_answer=user_text,
                audio_analysis_status="PENDING",
            )
            db.add(new_qa)
            await db.commit()
            await db.refresh(new_qa)
            eval_id = new_qa.id

        async def _bg_audio_metrics(e_id, audio, text):
            async with async_session_factory() as bg_db:
                await analyze_and_save_audio_metrics(bg_db, e_id, audio, text)
                
        asyncio.create_task(_bg_audio_metrics(eval_id, full_audio, user_text))
        
        asyncio.create_task(self._async_eval_single(eval_id, ctx.current_question, user_text))

        ctx.current_round += 1
        stage, raw_sys_prompt = ctx.state_machine.get_stage_prompt(ctx.current_round)

        sys_prompt = raw_sys_prompt
        if "{retrieved_questions}" in raw_sys_prompt:
            retrieved_nodes = dual_retriever.retrieve_questions(ctx.target_role, top_k=2)
            retrieved_text = dual_retriever.format_results(retrieved_nodes)
            sys_prompt = raw_sys_prompt.format(retrieved_questions=retrieved_text)

        await self._stream_llm_response(session_id, ctx, sys_prompt)


    async def handle_text_message(self, session_id: str, payload: TextMessagePayload):
        ctx = self.get_context(session_id)
        if not ctx:
            return

        user_text = payload.text.strip()
        if not user_text:
            return

        await self.send(
            session_id,
            WsServerMessage.from_payload(
                session_id=session_id, msg_type=WsMsgType.SYSTEM_STATUS,
                payload=SystemStatusPayload(status="thinking", message="解析文本并生成回复..."),
            )
        )

        ctx.add_memory("USER", user_text)

        async with async_session_factory() as db:
            db.add(DialogueMessage(
                session_id=session_id,
                round_seq=ctx.current_round,
                speaker="USER",
                content=user_text,
            ))
            await db.commit()

        async with async_session_factory() as db:
            new_qa = QaEvaluation(
                session_id=session_id,
                question_content=ctx.current_question,
                user_answer=user_text,
                audio_analysis_status="COMPLETED",
            )
            db.add(new_qa)
            await db.commit()
            await db.refresh(new_qa)
            eval_id = new_qa.id

        asyncio.create_task(self._async_eval_single(eval_id, ctx.current_question, user_text))

        ctx.current_round += 1
        stage, raw_sys_prompt = ctx.state_machine.get_stage_prompt(ctx.current_round)

        sys_prompt = raw_sys_prompt
        if "{retrieved_questions}" in raw_sys_prompt:
            retrieved_nodes = dual_retriever.retrieve_questions(ctx.target_role, top_k=2)
            retrieved_text = dual_retriever.format_results(retrieved_nodes)
            sys_prompt = raw_sys_prompt.format(retrieved_questions=retrieved_text)

        await self._stream_llm_response(session_id, ctx, sys_prompt)

    async def handle_stop_speaking(self, session_id: str, payload: StopSpeakingPayload):
        ctx = self.get_context(session_id)
        if ctx:
            ctx.cancel_event.set()


    async def _stream_llm_response(self, session_id: str, ctx: InterviewSessionContext, system_prompt: str):
        context_text = ctx.memory.build_context_window(ctx.history)
        
        user_prompt = f"【对话历史】\n{context_text}\n\n当前轮到你（[面试官]）开口了，请注意必须严格扮演面试官，直接接话往下聊，不要带前缀[面试官]："

        ctx.cancel_event.clear()
        
        chunk_id = f"msg-{ctx.current_round}"
        seq = 0
        full_ai_response = ""

        await self.send(
            session_id,
            WsServerMessage.from_payload(
                session_id=session_id, msg_type=WsMsgType.SYSTEM_STATUS,
                payload=SystemStatusPayload(status="listening", message="开始应答..."),
            )
        )

        try:
            async for text_piece in llm_client.chat_stream(system_prompt, user_prompt):
                if ctx.cancel_event.is_set():
                    break
                    
                full_ai_response += text_piece
                
                await self.send(
                    session_id,
                    WsServerMessage.from_payload(
                        session_id=session_id, msg_type=WsMsgType.TEXT_STREAM,
                        payload=TextStreamPayload(
                            chunk_id=chunk_id, seq=seq, text=text_piece, is_end=False
                        )
                    )
                )
                seq += 1
                await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"[WS Service LLM] 生成异常: {e}")

        await self.send(
            session_id,
            WsServerMessage.from_payload(
                session_id=session_id, msg_type=WsMsgType.TEXT_STREAM,
                payload=TextStreamPayload(
                    chunk_id=chunk_id, seq=seq, text="", is_end=True
                )
            )
        )

        ctx.current_question = full_ai_response
        ctx.add_memory("AI", full_ai_response)

        # ---- 持久化 AI 消息到数据库 ----
        async with async_session_factory() as db:
            db.add(DialogueMessage(
                session_id=session_id,
                round_seq=ctx.current_round,
                speaker="AI",
                content=full_ai_response,
            ))
            await db.commit()

    async def _async_eval_single(self, eval_id: str, q: str, a: str):
        res = await evaluator.evaluate_single_qa(q, a, "标准由大模型自判")
        async with async_session_factory() as db:
            db_eval = await db.get(QaEvaluation, eval_id)
            if db_eval:
                db_eval.technical_score = res["technical_score"]
                db_eval.correction_feedback = res["correction_feedback"]
                await db.commit()


# 全局单例管理器
manager = ConnectionManager()
