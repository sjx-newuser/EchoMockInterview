<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWebSocket } from '../../composables/useWebSocket'
import { useAudioRecorder } from '../../composables/useAudioRecorder'
import { getInterviewDetail } from '../../api/interview'
import ChatMessage from '../../components/common/ChatMessage.vue'
import AudioControls from '../../components/audio/AudioControls.vue'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id as string

const interviewInfo = ref<any>(null)
const messageListContainer = ref<HTMLElement | null>(null)

const { 
  messages, 
  status, 
  isConnected, 
  connect, 
  sendMessage,
  disconnect
} = useWebSocket(sessionId)

const { 
  isRecording, 
  startRecording, 
  stopRecording 
} = useAudioRecorder()

const fetchInterviewInfo = async () => {
  try {
    const data = await getInterviewDetail(sessionId)
    interviewInfo.value = data
    
    // Restore historical messages
    if (data.messages && data.messages.length > 0) {
      messages.value = data.messages.map((m: any) => ({
        id: m.id || String(Date.now()),
        speaker: m.speaker,
        content: m.content,
        isStreaming: false
      }))
    }

    // If successful, connect WebSocket
    connect()
  } catch (err) {
    console.error('Interview not found', err)
    router.push('/dashboard')
  }
}

const handleStart = () => {
  sendMessage('start_interview', { target_role: interviewInfo.value.target_role })
}

const handleSendAudio = async () => {
  const base64 = await stopRecording()
  if (base64) {
    // Add user message locally for UI
    messages.value.push({
      id: Date.now().toString(),
      speaker: 'USER',
      content: '(语音已发送)',
      isStreaming: false
    })
    
    sendMessage('audio_chunk', {
      seq: 0,
      audio_base64: base64,
      is_last: true
    })
  }
}

const inputText = ref('')

const handleSendText = () => {
  const text = inputText.value.trim()
  if (!text) return

  const localMsg = {
    id: Date.now().toString(),
    speaker: 'USER',
    content: text,
    isStreaming: false
  }
  messages.value.push(localMsg)

  const sent = sendMessage('text_message', { text })
  if (sent) {
    inputText.value = ''
  } else {
    // 发送失败：移除本地消息，保留输入内容
    messages.value = messages.value.filter(m => m.id !== localMsg.id)
    console.warn('[Interview] 消息发送失败，请检查连接状态')
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListContainer.value) {
    messageListContainer.value.scrollTop = messageListContainer.value.scrollHeight
  }
}

watch(messages, () => scrollToBottom(), { deep: true })

const handleFinish = () => {
  // Disconnect WebSocket gracefully
  disconnect()
  // Navigate to the report page, which triggers lazy report generation
  router.push(`/report/${sessionId}`)
}

onMounted(() => {
  fetchInterviewInfo()
})
</script>

<template>
  <div class="interview-room-container">
    <!-- Header -->
    <header class="room-header glass-panel">
      <div class="header-left">
        <button @click="router.push('/dashboard')" class="btn-back">← 返回</button>
        <div class="interview-meta" v-if="interviewInfo">
          <span class="role-name">{{ interviewInfo.target_role }}</span>
          <span class="dot">•</span>
          <span class="session-label">面试场次 #{{ sessionId.slice(0,8) }}</span>
        </div>
      </div>
      <div class="header-right">
        <div class="status-indicator" :class="status.status">
          <span class="status-dot"></span>
          {{ status.message }}
        </div>
        <button @click="handleFinish" class="btn-finish" v-if="isConnected">
          结束并查看报告
        </button>
      </div>
    </header>

    <!-- Chat Area -->
    <main class="chat-area" ref="messageListContainer">
      <div v-if="messages.length === 0" class="welcome-box">
        <div class="ai-avatar-large">AI</div>
        <h2>面试已就绪</h2>
        <p>点击下方按钮开始您的面试，AI 将为您主持开场。</p>
        <button @click="handleStart" class="btn-primary" v-if="isConnected && status.status === 'idle'">
          开始面试
        </button>
      </div>

      <ChatMessage 
        v-for="msg in messages" 
        :key="msg.id" 
        :msg="msg" 
      />
    </main>

    <!-- Control Bar -->
    <footer class="control-bar glass-panel">
      <div class="input-methods">
        <AudioControls 
          :status="status" 
          :is-recording="isRecording"
          @start-record="startRecording"
          @stop-record="handleSendAudio"
        />

        <div class="text-input-wrap" v-if="isConnected && (status.status === 'listening' || status.status === 'thinking')">
          <input 
            v-model="inputText" 
            @keyup.enter="handleSendText"
            type="text" 
            class="input-base"
            placeholder="或直接输入文字..."
          />
          <button @click="handleSendText" class="btn-primary" :disabled="!inputText.trim()">发送</button>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.interview-room-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  margin-bottom: 20px;
}

.btn-back {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
  color: var(--color-text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  margin-right: 16px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-back:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: translateX(-2px);
}

.btn-finish {
  background: #fff;
  border: 1px solid #ff4d4f;
  color: #ff4d4f;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  margin-left: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-finish:hover {
  background: #ff4d4f;
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.2);
}

.interview-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-name {
  font-weight: 700;
  font-size: 18px;
}

.session-label {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
}

.thinking .status-dot { background: #ffcc00; box-shadow: 0 0 8px #ffcc00; }
.listening .status-dot { background: var(--color-success); box-shadow: 0 0 8px var(--color-success); }

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.welcome-box {
  text-align: center;
  margin: auto;
  max-width: 400px;
}

.ai-avatar-large {
  width: 80px;
  height: 80px;
  background: var(--color-accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 900;
  margin: 0 auto 24px;
  box-shadow: 0 0 30px rgba(61, 127, 255, 0.4);
}

.control-bar {
  padding: 24px;
  margin-top: 20px;
}

.input-methods {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.text-input-wrap {
  display: flex;
  gap: 12px;
  align-items: center;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.text-input-wrap input {
  flex: 1;
}
</style>
