<script setup lang="ts">
defineProps<{
  msg: {
    id: string
    speaker: string
    content: string
    isStreaming: boolean
  }
}>()
</script>

<template>
  <div class="message-bubble" :class="msg.speaker">
    <div class="avatar">{{ msg.speaker === 'AI' ? '🤖' : '👤' }}</div>
    <div class="content">
      <div class="text">{{ msg.content }}</div>
      <div v-if="msg.isStreaming" class="typing-indicator">...</div>
    </div>
  </div>
</template>

<style scoped>
.message-bubble {
  display: flex;
  gap: 16px;
  max-width: 85%;
  animation: messageIn 0.3s ease-out;
}

@keyframes messageIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-bubble.USER {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.avatar {
  width: 40px;
  height: 40px;
  background: var(--color-bg-panel);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.content {
  background: var(--color-bg-panel);
  padding: 16px 20px;
  border-radius: var(--radius-md);
  line-height: 1.6;
  border: 1px solid var(--color-border);
}

.USER .content {
  background: var(--color-accent);
  border-color: transparent;
}

.typing-indicator {
  font-size: 20px;
  line-height: 1;
  color: var(--color-accent);
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}
</style>
