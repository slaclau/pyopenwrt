<script setup lang="ts">
import type { Status } from '@/sdk'
import NetworksView from './NetworksView.vue'
import WirelessView from './WirelessView.vue'

defineProps<{
  status: Status | null
}>()
</script>

<template>
  <el-tabs tab-position="left" :stretch="true">
    <el-tab-pane label="Networks" name="networks">
      <NetworksView :status="status" />
    </el-tab-pane>
    <el-tab-pane label="WiFi" name="wireless">
      <WirelessView :status="status" />
    </el-tab-pane>
  </el-tabs>
</template>
