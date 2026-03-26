<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import { login } from '../../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  errorMsg.value = ''
  
  try {
    const data: any = await login({
      username: username.value,
      password: password.value
    })
    
    authStore.setToken(data.access_token)
    // Fetch user info after login
    await authStore.fetchCurrentUser()
    
    router.push('/dashboard')
  } catch (err: any) {
    errorMsg.value = err.message || '登录失败，请检查用户名或密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="glass-panel auth-card">
      <div class="auth-header">
        <h1 class="brand-title">Echo Mock</h1>
        <p class="brand-subtitle">AI 驱动的多模态面试系统</p>
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="username" 
            type="text" 
            class="input-base" 
            placeholder="输入您的用户名"
            required
          />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="password" 
            type="password" 
            class="input-base" 
            placeholder="••••••••"
            required
          />
        </div>

        <div v-if="errorMsg" class="error-banner">
          {{ errorMsg }}
        </div>

        <button type="submit" class="btn-primary full-width" :disabled="loading">
          {{ loading ? '进入中...' : '登录系统' }}
        </button>
      </form>

      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="link-text">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.auth-header {
  text-align: center;
  margin-bottom: 40px;
}

.brand-title {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #fff 0%, #a0a0ff 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}

.brand-subtitle {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  padding-left: 4px;
}

.full-width {
  width: 100%;
  margin-top: 10px;
}

.error-banner {
  background: rgba(234, 76, 76, 0.1);
  color: var(--color-danger);
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  text-align: center;
  border: 1px solid rgba(234, 76, 76, 0.2);
}

.auth-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.link-text {
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 600;
  margin-left: 8px;
  transition: var(--transition-fast);
}

.link-text:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}
</style>
