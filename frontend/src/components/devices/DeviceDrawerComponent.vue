<script setup lang="ts">
import type { DeviceStatusWithDevice } from 'controller/sdk/types.gen'
import DeviceOverview from 'controller/components/devices/overview/DeviceOverview.vue'
import DeviceSettings from 'controller/components/devices/settings/DeviceSettings.vue'
import DeviceCommands from 'controller/components/devices/overview/DeviceCommands.vue'

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
