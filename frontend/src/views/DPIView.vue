<script setup lang="ts">
import { client } from '@/client'
import {
  getHostLastHourStatsNetifyStatsByHostLastDayGet,
  type HostTimeStats,
} from '@/sdk'

import { onMounted, onUnmounted, ref, type Ref } from 'vue'

import { Chart as ChartJS, registerables } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import ChartDataLabels from 'chartjs-plugin-datalabels';
import DPITable from './DPITable.vue'
import { getApplicationName, setIntervalImmediate } from '@/utils.ts'
ChartJS.register(...registerables)
ChartJS.register(ChartDataLabels)

let timer: number
const dpi_data: Ref<HostTimeStats | null> = ref(null)
const hosts_sum: Ref<number> = ref(0)
const categories_sum: Ref<number> = ref(0)

onMounted(() => {
  timer = setIntervalImmediate(() => {
    getHostLastHourStatsNetifyStatsByHostLastDayGet({ client }).then((res) => {
      if (res.data) {
        dpi_data.value = res.data
        hosts_sum.value = dpi_data.value.hosts.reduce(
          (prev, curr) => prev + curr.download + curr.upload,
          0,
        )
        categories_sum.value = dpi_data.value.categories.reduce(
          (prev, curr) => prev + curr.download + curr.upload,
          0,
        )
      } else {
        console.log('no data yet')
      }
    })
  }, 3000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<template>
  <el-row :gutter="20">
    <el-col :xs="24" :sm="12" :m="8" :lg="6" :xl="4">
      <el-card header="Applications">
        <Doughnut :data="{
          labels: dpi_data?.categories.map((cat) =>
            getApplicationName(cat.application, cat.protocol),
          ),
          datasets: [
            {
              data: dpi_data ? dpi_data?.categories.map(
                (cat) => cat.download + cat.upload,
              ) : [],
            },
          ],
        }" :options="{
          responsive: true,
          plugins: {
            colors: { forceOverride: true },
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: function (context) {
                  let label = context.dataset.label || ''

                  if (label) {
                    label += ': '
                  }
                  if (context.parsed !== null) {
                    label += new Intl.NumberFormat('en-GB', {
                      style: 'percent',
                    }).format(context.parsed / categories_sum)
                  }
                  return label
                },
              },
            },
            datalabels: {
              color: 'white',
              font: { weight: 'bold' },
              formatter: (function (value, context) {
                return value / categories_sum > 0.05 ? context.chart.data.labels?.[context.dataIndex] : '';
              })
            }
          },
        }" />
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :m="8" :lg="6" :xl="4">
      <el-card header="Hosts">
        <Doughnut :data="{
          labels: dpi_data?.hosts.map((cat) => `${cat.mac} / ${cat.ip}`),
          datasets: [
            { data: dpi_data ? dpi_data?.hosts.map((cat) => cat.download + cat.upload) : [] },
          ],
        }" :options="{
          responsive: true,
          plugins: {
            colors: { forceOverride: true },
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: function (context) {
                  let label = context.dataset.label || ''

                  if (label) {
                    label += ': '
                  }
                  if (context.parsed !== null) {
                    label += new Intl.NumberFormat('en-GB', {
                      style: 'percent',
                    }).format(context.parsed / hosts_sum)
                  }
                  return label
                },
              },
            },
            datalabels: {
              color: 'white',
              font: { weight: 'bold' },
              formatter: (function (value, context) {
                return value / hosts_sum > 0.05 ? context.chart.data.labels?.[context.dataIndex] : '';
              })
            }
          },
        }" />
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="24" :m="8" :lg="12" :xl="16">
      <DPITable :dpi_data="dpi_data" />
    </el-col>
  </el-row>
</template>
