import { ref } from 'vue'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const mediaRecorder = ref<MediaRecorder | null>(null)
  const audioChunks = ref<Blob[]>([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder.value = new MediaRecorder(stream)
      audioChunks.value = []

      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.value.push(event.data)
        }
      }

      mediaRecorder.value.start()
      isRecording.value = true
    } catch (err) {
      console.error('Failed to access microphone:', err)
      alert('无法访问麦克风，请检查权限设置')
    }
  }

  const stopRecording = (): Promise<string> => {
    return new Promise((resolve) => {
      if (!mediaRecorder.value || !isRecording.value) {
        resolve('')
        return
      }

      mediaRecorder.value.onstop = async () => {
        const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' })
        const base64 = await blobToBase64(audioBlob)
        
        // Clean up stream
        mediaRecorder.value?.stream.getTracks().forEach(track => track.stop())
        isRecording.value = false
        
        resolve(base64)
      }

      mediaRecorder.value.stop()
    })
  }

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = reject
      reader.onload = () => {
        const result = reader.result as string
        // Remove data:audio/wav;base64, prefix
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.readAsDataURL(blob)
    })
  }

  return {
    isRecording,
    startRecording,
    stopRecording
  }
}
