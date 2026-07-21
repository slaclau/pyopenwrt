<script setup lang="ts">
import type { DeviceStatusWithDevice } from '@/sdk'
import DeviceIcon from 'controller/components/devices/DeviceIcon.vue'
defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()
</script>

<template>
  <el-card>
    <div>
      <DeviceIcon :device="device?.device" /> <strong>{{ device?.device.hostname }}</strong>
    </div>
    <div>
      <small>
        {{ device?.device.model }}
      </small>
    </div>
    <div style="text-align: right" class="subtitle">
      {{ device?.last_ip }}
    </div>
  </el-card>
</template>
