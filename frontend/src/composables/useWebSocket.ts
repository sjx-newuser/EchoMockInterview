import { ref, onUnmounted } from 'vue'

export function useWebSocket(sessionId: string) {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const messages = ref<any[]>([])
  const status = ref({ status: 'connecting', message: '正在建立连接...' })

  const connect = () => {
    // Protocol detection: use ws:// for localhost dev, wss:// if https
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/ws/${sessionId}`

    socket.value = new WebSocket(wsUrl)

    socket.value.onopen = () => {
      isConnected.value = true
      console.log('[WS] Connected')
    }

    socket.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleMessage(data)
    }

    socket.value.onclose = () => {
      isConnected.value = false
      status.value = { status: 'disconnected', message: '连接已断开' }
    }

    socket.value.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }

  const handleMessage = (msg: any) => {
    const { type, payload } = msg

    if (type === 'system_status') {
      status.value = payload
    } else if (type === 'text_stream') {
      updateStreamingMessage(payload)
    }
  }

  const updateStreamingMessage = (payload: any) => {
    const { chunk_id, text, is_end } = payload
    
    // Find or create the message bubble
    let msg = messages.value.find(m => m.id === chunk_id)
    
    if (!msg) {
      msg = {
        id: chunk_id,
        speaker: 'AI',
        content: '',
        isStreaming: true
      }
      messages.value.push(msg)
    }

    msg.content += text
    if (is_end) {
      msg.isStreaming = false
    }
  }

  const sendMessage = (type: string, payload: any) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify({
        session_id: sessionId,
        type,
        payload
      }))
    }
  }

  const disconnect = () => {
    socket.value?.close()
  }

  onUnmounted(() => disconnect())

  return {
    isConnected,
    messages,
    status,
    connect,
    sendMessage,
    disconnect
  }
}
