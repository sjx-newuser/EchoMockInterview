<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import { register } from '../../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMsg = ref('')
const loading = ref(false)

const handleRegister = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  errorMsg.value = ''
  
  try {
    const data: any = await register({
      username: username.value,
      password: password.value
    })
    
    authStore.setToken(data.access_token)
    // Fetch user info after registration
    await authStore.fetchCurrentUser()
    
    router.push('/dashboard')
  } catch (err: any) {
    errorMsg.value = err.message || '注册失败，用户名可能已存在'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="glass-panel auth-card">
      <div class="auth-header">
        <h1 class="brand-title">加入 Echo Mock</h1>
        <p class="brand-subtitle">开启您的 AI 模拟面试之旅</p>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="username" 
            type="text" 
            class="input-base" 
            placeholder="取一个好听的名字"
            required
          />
        </div>

        <div class="form-group">
          <label>设置密码</label>
          <input 
            v-model="password" 
            type="password" 
            class="input-base" 
            placeholder="建议包含字母与数字"
            required
          />
        </div>

        <div class="form-group">
          <label>确认密码</label>
          <input 
            v-model="confirmPassword" 
            type="password" 
            class="input-base" 
            placeholder="再次输入密码"
            required
          />
        </div>

        <div v-if="errorMsg" class="error-banner">
          {{ errorMsg }}
        </div>

        <button type="submit" class="btn-primary full-width" :disabled="loading">
          {{ loading ? '注册中...' : '立即注册' }}
        </button>
      </form>

      <div class="auth-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="link-text">返回登录</router-link>
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
  animation: slideIn 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes slideIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.auth-header {
  text-align: center;
  margin-bottom: 40px;
}

.brand-title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: white;
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
  gap: 20px;
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
