<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  dimensionScores: any[]
}>()

const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null

const initChart = async () => {
  await nextTick()
  if (!chartRef.value || !props.dimensionScores?.length) return

  if (myChart) {
    myChart.dispose()
  }

  myChart = echarts.init(chartRef.value)
  
  const indicator = props.dimensionScores.map((d: any) => ({
    name: d.name,
    max: 100
  }))

  const data = props.dimensionScores.map((d: any) => d.score)

  const option = {
    backgroundColor: 'transparent',
    radar: {
      indicator: indicator,
      radius: '65%',
      splitNumber: 4,
      axisName: {
        color: '#666',
        fontSize: 14
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.08)'
        }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(0, 0, 0, 0.02)', 'rgba(0, 0, 0, 0.05)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.08)'
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: data,
            name: '能力分布',
            symbol: 'none',
            lineStyle: {
              color: '#3d7fff',
              width: 2
            },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { color: 'rgba(61, 127, 255, 0.6)', offset: 0 },
                { color: 'rgba(61, 127, 255, 0.1)', offset: 1 }
              ])
            }
          }
        ]
      }
    ]
  }

  myChart.setOption(option)
}

const handleResize = () => {
  if (myChart) {
    myChart.resize()
  }
}

watch(() => props.dimensionScores, () => {
  initChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (myChart) {
    myChart.dispose()
  }
})
</script>

<template>
  <div ref="chartRef" class="radar-chart"></div>
</template>

<style scoped>
.radar-chart {
  height: 320px;
  width: 100%;
}
</style>
