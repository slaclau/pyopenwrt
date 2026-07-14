<script setup lang="ts">
import { client } from './client'
import { getStatusStatusGet, type Status } from './sdk'
import DevicesView from './views/DevicesView.vue'
import OverviewView from './views/OverviewView.vue'
import SettingsView from './views/SettingsView.vue'
import DPIView from './views/DPIView.vue'

import SvgIcon from '@jamescoyle/vue-icon'
import {
  mdiMonitorDashboard,
  mdiServerOutline,
  mdiMonitorCellphone,
  mdiCog,
  mdiChartLine,
  mdiThemeLightDark,
} from '@mdi/js'

import { useDark, useToggle } from '@vueuse/core'
import { onMounted, onUnmounted, ref, type Ref } from 'vue'

let status: Ref<Status> = ref({})
let timer: number
const isDark = useDark()
const toggleDark = useToggle(isDark)

onMounted(() => {
  timer = setInterval(() => {
    getStatusStatusGet({ client }).then((res) => {
      if (res.data) {
        status.value = res.data
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
  <el-container>
    <el-header>
      <h1>
        OpenWrt Controller
        <span style="float: right"
          ><el-button @click="toggleDark()"><svg-icon type="mdi" :path="mdiThemeLightDark" :size="24"/></el-button></span
        >
      </h1>
    </el-header>
    <el-main>
      <el-tabs :stretch="true">
        <el-tab-pane name="overview">
          <template #label>
            <svg-icon type="mdi" :path="mdiMonitorDashboard" :size="24" />
          </template>
          <OverviewView />
        </el-tab-pane>
        <el-tab-pane name="devices">
          <template #label>
            <svg-icon type="mdi" :path="mdiServerOutline" :size="24" />
          </template>
          <DevicesView :devices="status.device_status" />
        </el-tab-pane>
        <el-tab-pane name="clients">
          <template #label>
            <svg-icon type="mdi" :path="mdiMonitorCellphone" :size="24" />
          </template>
        </el-tab-pane>
        <el-tab-pane label="DPI" name="dpi">
          <template #label>
            <svg-icon type="mdi" :path="mdiChartLine" :size="24" />
          </template>
          <DPIView />
        </el-tab-pane>
        <el-tab-pane name="settings">
          <template #label>
            <svg-icon type="mdi" :path="mdiCog" :size="24" /> </template
          ><SettingsView :status="status"
        /></el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>
