<script setup lang="ts">
  defineProps<{
  status: { status: string; message: string }
  isRecording: boolean
}>()

const emit = defineEmits<{
  (e: 'start-record'): void
  (e: 'stop-record'): void
}>()
</script>

<template>
  <div class="controls-inner">
    <div v-if="status.status === 'thinking'" class="thinking-ui">
      <div class="pulse-loader"></div>
      <span>AI 正在思考中...</span>
    </div>

    <div v-else-if="status.status === 'listening'" class="action-buttons">
      <button 
        v-if="!isRecording" 
        @mousedown="emit('start-record')" 
        @touchstart="emit('start-record')"
        class="btn-primary record-btn"
      >
        <span class="icon">🎙️</span> 按住说话
      </button>
      
      <button 
        v-else 
        @mouseup="emit('stop-record')" 
        @touchend="emit('stop-record')"
        class="btn-primary recording-active"
      >
        <div class="recording-pulse"></div>
        松开结束
      </button>
    </div>
    
    <div v-else class="idle-info">
      等待下一步指令
    </div>
  </div>
</template>

<style scoped>
.controls-inner {
  display: flex;
  justify-content: center;
  align-items: center;
}

.record-btn {
  padding: 16px 40px;
  font-size: 18px;
  border-radius: 30px;
}

.recording-active {
  padding: 16px 40px;
  font-size: 18px;
  border-radius: 30px;
  background: var(--color-danger);
  display: flex;
  align-items: center;
  gap: 12px;
}

.recording-pulse {
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.thinking-ui {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text-secondary);
}

.pulse-loader {
  width: 24px;
  height: 24px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.idle-info {
  color: var(--color-text-secondary);
}
</style>
