<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import { listInterviews, createInterview, deleteInterview, toggleFavorite } from '../../api/interview'
import InterviewCard from '../../components/common/InterviewCard.vue'

const router = useRouter()
const authStore = useAuthStore()

const interviews = ref<any[]>([])
const loading = ref(false)
const targetRole = ref('')
const creating = ref(false)

const fetchInterviews = async () => {
  loading.value = true
  try {
    interviews.value = await listInterviews() as any[]
  } catch (error) {
    console.error('Failed to fetch interviews:', error)
  } finally {
    loading.value = false
  }
}

const handleStartInterview = async () => {
  if (!targetRole.value.trim()) return
  
  creating.value = true
  try {
    const data: any = await createInterview({
      target_role: targetRole.value
    })
    router.push(`/interview/${data.id}`)
  } catch (error) {
    console.error('Failed to start interview:', error)
  } finally {
    creating.value = false
  }
}

const handleLogout = () => {
  authStore.clearAuth()
  router.push('/login')
}

const handleDelete = async (sessionId: string) => {
  try {
    await deleteInterview(sessionId)
    interviews.value = interviews.value.filter(i => i.id !== sessionId)
  } catch (error) {
    console.error('Failed to delete interview:', error)
  }
}

const handleToggleFavorite = async (sessionId: string) => {
  try {
    const updated = await toggleFavorite(sessionId)
    const index = interviews.value.findIndex(i => i.id === sessionId)
    if (index !== -1) {
      interviews.value[index].is_favorite = updated.is_favorite
    }
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
  }
}

onMounted(() => {
  fetchInterviews()
})
</script>

<template>
  <div class="dashboard-container">
    <nav class="top-nav">
      <div class="nav-brand">Echo Mock</div>
      <div class="user-info">
        <span class="username">{{ authStore.user?.username }}</span>
        <button @click="handleLogout" class="btn-logout">退出</button>
      </div>
    </nav>

    <main class="dashboard-content">
      <!-- Start Panel -->
      <section class="start-panel glass-panel">
        <div class="section-title">发起新面试</div>
        <p class="section-desc">告诉 AI 您想挑战的职位，我们将为您量身定制面试方案。</p>
        
        <div class="start-form">
          <input 
            v-model="targetRole" 
            type="text" 
            class="input-base" 
            placeholder="例如: 后端开发工程师, 架构师, 测试..."
          />
          <button @click="handleStartInterview" class="btn-primary" :disabled="creating">
            {{ creating ? '创建中...' : '开始模拟面试' }}
          </button>
        </div>
      </section>

      <!-- History List -->
      <section class="history-list">
        <div class="section-header">
          <h2 class="section-title">面试记录</h2>
          <button @click="fetchInterviews" class="btn-refresh" :disable="loading">
            <span class="refresh-icon" :class="{ 'spinning': loading }">🔄</span>
            刷新
          </button>
        </div>

        <div v-if="loading" class="loading-state">载入中...</div>
        
        <div v-else-if="interviews.length === 0" class="empty-state glass-panel">
          还没有面试记录，开始您的第一次挑战吧！
        </div>

        <div v-else class="grid-layout">
          <InterviewCard 
            v-for="item in interviews" 
            :key="item.id" 
            :item="item"
            @click="router.push(`/interview/${item.id}`)"
            @view-report="router.push(`/report/${item.id}`)"
            @continue="router.push(`/interview/${item.id}`)"
            @delete="handleDelete(item.id)"
            @toggle-favorite="handleToggleFavorite(item.id)"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  width: 100%;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-bottom: 40px;
}

.nav-brand {
  font-size: 24px;
  font-weight: 800;
  color: var(--color-accent);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-weight: 500;
  color: var(--color-text-secondary);
}

.btn-logout {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.start-panel {
  padding: 40px;
  text-align: center;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}

.section-desc {
  color: var(--color-text-secondary);
  margin-bottom: 32px;
}

.start-form {
  display: flex;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid var(--color-border);
  padding: 8px 16px;
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-refresh:hover {
  background: #fcfcfc;
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-refresh:active {
  transform: scale(0.98);
}

.refresh-icon {
  display: inline-block;
  font-size: 14px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
