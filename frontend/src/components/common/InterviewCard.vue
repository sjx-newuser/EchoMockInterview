<script setup lang="ts">
defineProps<{
  item: any
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'view-report'): void
  (e: 'continue'): void
}>()

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
      <span class="role-badge">{{ item.target_role }}</span>
      <span class="status-tag" :class="item.status">{{ item.status }}</span>
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
  margin-bottom: 16px;
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
