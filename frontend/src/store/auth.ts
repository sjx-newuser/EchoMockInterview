import { defineStore } from 'pinia'
import { getMe } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    },
    
    setUser(user: any) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },

    clearAuth() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    async fetchCurrentUser() {
      if (!this.token) return null
      try {
        const userData = await getMe()
        this.setUser(userData)
        return userData
      } catch (error) {
        this.clearAuth()
        throw error
      }
    }
  }
})
