<script setup lang="ts">
import type { DeviceStatusWithDevice } from '../../sdk/types.gen'
import DeviceOverview from './overview/DeviceOverview.vue'
import DeviceSettings from './settings/DeviceSettings.vue'
import DeviceCommands from './overview/DeviceCommands.vue'

defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()
</script>

<template>
  <el-tabs v-if="device !== null">
    <el-tab-pane label="Overview">
      <DeviceOverview :device="device" />
    </el-tab-pane>
    <el-tab-pane v-if="device?.device.adopted" label="Settings">
      <DeviceSettings :device="device" />
      <DeviceCommands :device="device" />
    </el-tab-pane>
  </el-tabs>
</template>
