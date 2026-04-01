<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  item: any
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'view-report'): void
  (e: 'continue'): void
  (e: 'delete'): void
  (e: 'toggle-favorite'): void
}>()

const menuOpen = ref(false)

const toggleMenu = (e: Event) => {
  e.stopPropagation()
  menuOpen.value = !menuOpen.value
}

const closeMenu = () => {
  menuOpen.value = false
}

const handleAction = (action: 'delete' | 'favorite', e: Event) => {
  e.stopPropagation()
  closeMenu()
  if (action === 'delete') {
    if (confirm('确定要删除这场面试记录吗？此操作不可撤销。')) {
      emit('delete')
    }
  } else {
    emit('toggle-favorite')
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="card glass-panel" @click="emit('click')">
    <div class="card-header">
      <div class="header-left">
        <span class="role-badge">{{ item.target_role }}</span>
        <span v-if="item.is_favorite" class="fav-star">★</span>
      </div>
      <div class="header-right">
        <span class="status-tag" :class="item.status">{{ item.status }}</span>
        <div class="menu-container">
          <button class="menu-dots-btn" @click.stop="toggleMenu">•••</button>
          <transition name="fade">
            <div v-if="menuOpen" class="menu-dropdown glass-panel" @mouseleave="closeMenu">
              <button class="menu-item" @click="handleAction('favorite', $event)">
                {{ item.is_favorite ? '取消收藏' : '加入收藏' }}
              </button>
              <button class="menu-item danger" @click="handleAction('delete', $event)">
                彻底删除
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
    <div class="card-body">
      <div class="item-meta">时间: {{ formatDate(item.start_time) }}</div>
      <div class="item-score" v-if="item.overall_score">
        得分: <span class="score-num">{{ item.overall_score }}</span>
      </div>
    </div>
    <div class="card-footer">
      <button v-if="item.overall_score" class="btn-secondary small" @click.stop="emit('view-report')">
        查看报告
      </button>
      <button v-else class="btn-primary small" @click.stop="emit('continue')">
        继续面试
      </button>
    </div>
  </div>
</template>

<style scoped>
.card {
  padding: 24px;
  cursor: pointer;
  transition: transform var(--transition-normal);
}

.card:hover {
  transform: translateY(-4px);
  border-color: var(--color-border-focus);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fav-star {
  color: #ffcc00;
  font-size: 18px;
  text-shadow: 0 0 10px rgba(255, 204, 0, 0.4);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-container {
  position: relative;
}

.menu-dots-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 14px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.menu-dots-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text-primary);
}

.menu-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 10;
  min-width: 120px;
  padding: 8px;
  margin-top: 8px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  background: none;
  border: none;
  color: var(--color-text-primary);
  padding: 8px 12px;
  text-align: left;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.menu-item.danger {
  color: #ff4d4f;
}

.menu-item.danger:hover {
  background: rgba(255, 77, 79, 0.1);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.role-badge {
  font-weight: 700;
  font-size: 18px;
}

.status-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0,0,0,0.05);
}

.status-tag.COMPLETED { color: var(--color-success); background: rgba(46, 160, 67, 0.1); }
.status-tag.ONGOING { color: var(--color-accent); background: rgba(61, 127, 255, 0.1); }

.card-body {
  margin-bottom: 24px;
}

.item-meta {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.item-score {
  margin-top: 8px;
}

.score-num {
  font-size: 20px;
  font-weight: 800;
  color: var(--color-accent);
}

.card-footer {
  display: flex;
  gap: 12px;
}

.small {
  padding: 8px 16px;
  font-size: 13px;
}
</style>
