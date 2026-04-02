import os
import sys
# 将项目根目录加入 Python 搜索路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.db.models import User, InterviewSession, DialogueMessage, QaEvaluation, SessionStatus, SpeakerRole, AudioAnalysisStatus
from app.db.database import async_session_factory
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    async with async_session_factory() as db:
        # 1. Create or get user
        from sqlalchemy import select
        user = (await db.execute(select(User).where(User.username == "demo_user"))).scalar_one_or_none()
        if not user:
            user = User(username="demo_user", password_hash=pwd_context.hash("123456"))
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"Created user: {user.username}")
        else:
            print(f"User already exists: {user.username}")

        # 2. Create InterviewSession
        session = InterviewSession(
            user_id=user.id,
            target_role="Java 后端开发工程师",
            status=SessionStatus.COMPLETED,
            overall_score=88.5,
            dimension_scores=[
                {"name": "技术深度", "score": 90},
                {"name": "逻辑表达", "score": 85},
                {"name": "沟通能力", "score": 88},
                {"name": "项目经验", "score": 85},
                {"name": "应变能力", "score": 92}
            ],
            comprehensive_report="# 面试深度复盘\n\n### 🌟 综合评价\n候选人展现了扎实的 Java 基础和优秀的系统设计能力，特别是在并发处理和微服务架构方面有深入理解。沟通表达清晰，逻辑严密，能够准确抓住问题的核心。\n\n### 💡 亮点\n- 对 JVM 内存模型和垃圾回收机制理解深刻。\n- 熟悉常见高并发场景的解决方案（如分布式锁、消息队列削峰）。\n\n### 🎯 改进建议\n- 在解释一些底层原理时，可以尝试结合具体的业务场景进行横向拓展对比。"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        # 3. Create Dialogue Messages
        messages = [
            (SpeakerRole.AI, "你好，我是今天的面试官。请简单做一个自我介绍吧。"),
            (SpeakerRole.USER, "面试官好，我叫张三，拥有三年Java后端开发经验，曾参与过千万级高并发电商系统的核心交易链路重构，熟悉 Spring Cloud 组件、Redis、MySQL 以及 Kafka 消息队列。"),
            (SpeakerRole.AI, "好的。你提到参与过高并发电商系统的交易链路重构，能具体讲讲在订单防超卖方面你们是怎么设计的吗？"),
            (SpeakerRole.USER, "我们使用了 Redis 和 Lua 脚本来实现库存的原子扣减，同时结合了 RocketMQ 发送半事务消息，确保本地订单状态和缓存以及下游系统的最终一致性。"),
            (SpeakerRole.AI, "如果 Redis 宕机了，你会怎么处理来保证系统依然可用？"),
            (SpeakerRole.USER, "我们会有一套降级策略，主库宕机切换从库，如果整个 Redis 哨兵集群不可用，我们会降级到本地 Guava Cache，同时限制请求的速率（限流），保护 MySQL 数据库不被打垮。")
        ]
        
        for i, (speaker, content) in enumerate(messages):
            msg = DialogueMessage(
                session_id=session.id,
                round_seq=i,
                speaker=speaker,
                content=content
            )
            db.add(msg)
            
        # 4. Create QA Evaluations
        evals = [
            QaEvaluation(
                session_id=session.id,
                question_content="你提到参与过高并发电商系统的交易链路重构，能具体讲讲在订单防超卖方面你们是怎么设计的吗？",
                user_answer="我们使用了 Redis 和 Lua 脚本来实现库存的原子扣减，同时结合了 RocketMQ 发送半事务消息，确保本地订单状态和缓存以及下游系统的最终一致性。",
                audio_analysis_status=AudioAnalysisStatus.COMPLETED,
                speech_rate=180.5,
                pause_ratio=0.12,
                technical_score=95,
                correction_feedback="回答非常准确，结合 Lua 脚本和消息中间件是业界的标准做法。如果能补充一下在极端情况下的回滚补偿机制就更完美了。"
            ),
            QaEvaluation(
                session_id=session.id,
                question_content="如果 Redis 宕机了，你会怎么处理来保证系统依然可用？",
                user_answer="我们会有一套降级策略，主库宕机切换从库，如果整个 Redis 哨兵集群不可用，我们会降级到本地 Guava Cache，同时限制请求的速率（限流），保护 MySQL 数据库不被打垮。",
                audio_analysis_status=AudioAnalysisStatus.COMPLETED,
                speech_rate=165.2,
                pause_ratio=0.15,
                technical_score=85,
                correction_feedback="思路清晰，具备高可用的底线思维（限流和本地降级）。不过在多节点服务下，本地缓存会导致数据一致性问题，建议补充下这块的权衡考虑。"
            )
        ]
        db.add_all(evals)
        await db.commit()
        
        print(f"Successfully created demo interview session: {session.id}")

if __name__ == "__main__":
    asyncio.run(main())
