<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getReport } from '../../api/report'
import RadarChart from '../../components/chart/RadarChart.vue'

const parseMarkdown = (text: string) => {
  if (!text) return ''
  return text
    // Headings
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*)\*\*/gm, '<strong>$1</strong>')
    // Lists
    .replace(/^\s*-\s+(.*$)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gms, '<ul>$1</ul>')
    .replace(/<\/ul>\s*<ul>/g, '')
    // Numbered Lists
    .replace(/^\s*\d+\.\s+(.*$)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gms, '<ol>$1</ol>')
    .replace(/<\/ol>\s*<ol>/g, '')
    // Paragraphs / Line breaks
    .replace(/\n\n/g, '<br/><br/>')
}

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id as string

const report = ref<any>(null)
const loading = ref(true)

const fetchReport = async () => {
  loading.value = true
  try {
    report.value = await getReport(sessionId)
  } catch (error) {
    console.error('Failed to fetch report:', error)
  } finally {
    loading.value = false
  }
}

const renderedReport = computed(() => {
  return report.value?.comprehensive_report ? parseMarkdown(report.value.comprehensive_report) : ''
})

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="report-container">
    <header class="report-header">
      <button @click="router.push('/dashboard')" class="btn-back">← 返回看板</button>
      <h1 class="page-title">面试深度复盘</h1>
    </header>

    <div v-if="loading" class="loading-full">
      <div class="spinner"></div>
      <p>AI 正在为您整理面试表现...</p>
    </div>

    <main v-else-if="report" class="report-content">
      <!-- Overview Card -->
      <section class="overview-section grid-2">
        <div class="score-card glass-panel">
          <div class="score-header">综合评分</div>
          <div class="score-display">
            <span class="score-total">{{ report.overall_score }}</span>
            <span class="score-max">/100</span>
          </div>
          <div class="score-status">
            {{ report.overall_score >= 80 ? '卓越表现' : report.overall_score >= 60 ? '良好表现' : '尚需努力' }}
          </div>
        </div>

        <div class="radar-card glass-panel">
          <div class="section-subtitle">多维度能力分布</div>
          <RadarChart v-if="report.dimension_scores" :dimension-scores="report.dimension_scores" />
        </div>
      </section>

      <!-- Detailed Analysis -->
      <section class="analysis-section glass-panel">
        <h2 class="section-title">综合评价报告</h2>
        <div class="markdown-body" v-html="renderedReport"></div>
      </section>

      <!-- Questions Breakdown -->
      <section class="qa-section">
        <h2 class="section-title">逐题复盘</h2>
        <div class="qa-list">
          <div v-for="(item, idx) in report.evaluations" :key="item.id" class="qa-item glass-panel">
            <div class="qa-header">
              <span class="qa-index">Q{{ Number(idx) + 1 }}</span>
              <span class="qa-score" v-if="item.technical_score">得分: {{ item.technical_score }}</span>
            </div>
            <div class="qa-body">
              <div class="qa-question"><strong>问：</strong>{{ item.question_content }}</div>
              <div class="qa-answer"><strong>答：</strong>{{ item.user_answer || '(未作答)' }}</div>
              <div class="qa-feedback" v-if="item.correction_feedback">
                <strong>改进建议：</strong> {{ item.correction_feedback }}
              </div>
            </div>
            <div class="qa-audio-meta" v-if="item.speech_rate">
              语速: {{ item.speech_rate?.toFixed(1) }} 字/秒 | 停顿比: {{ (item.pause_ratio * 100).toFixed(0) }}%
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.report-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 20px;
}

.report-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 40px;
}

.page-title {
  font-size: 28px;
  font-weight: 800;
}

.btn-back {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
  color: var(--color-text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-back:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: translateX(-2px);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 24px;
}

.score-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.score-header {
  font-size: 16px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
}

.score-total {
  font-size: 84px;
  font-weight: 900;
  color: var(--color-accent);
  line-height: 1;
}

.score-max {
  color: var(--color-text-secondary);
  font-size: 20px;
}

.score-status {
  margin-top: 24px;
  padding: 6px 16px;
  background: var(--color-bg-panel);
  border-radius: 20px;
  font-weight: 600;
}

.radar-card {
  padding: 32px;
  min-height: 400px;
}

.section-subtitle {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
}

.radar-chart {
  height: 320px;
  width: 100%;
}

.analysis-section {
  margin-top: 40px;
  padding: 40px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 24px;
}

.markdown-body {
  line-height: 1.8;
  color: var(--color-text-primary);
}

.markdown-body :deep(h2) {
  font-size: 1.25rem;
  margin: 24px 0 16px;
  color: var(--color-accent);
}

.markdown-body :deep(h3) {
  font-size: 1.1rem;
  margin: 20px 0 12px;
}

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 16px 0;
}

.markdown-body :deep(li) {
  margin-bottom: 8px;
}

.markdown-body :deep(strong) {
  color: var(--color-accent);
  font-weight: 700;
}

.qa-section {
  margin-top: 40px;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.qa-item {
  padding: 24px;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.qa-index {
  font-weight: 800;
  color: var(--color-accent);
}

.qa-score {
  font-size: 13px;
  font-weight: 600;
}

.qa-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 15px;
}

.qa-feedback {
  margin-top: 8px;
  padding: 12px;
  background: rgba(61, 127, 255, 0.05);
  border-left: 3px solid var(--color-accent);
  color: var(--color-text-secondary);
  font-size: 14px;
}

.qa-audio-meta {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.loading-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: rotate 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}
</style>
