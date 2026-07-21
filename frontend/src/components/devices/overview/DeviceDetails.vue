<script setup lang="ts">
import type { DeviceStatusWithDevice } from 'controller/sdk/types.gen'
import { formatTime } from 'controller/utils'
import DetailsRow from 'controller/components/DetailsRow.vue'
defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()
</script>

<template>
  <el-card>
    <DetailsRow :value="device?.device.model" name="Model" />
    <DetailsRow :value="device?.last_ip" name="IP Address" />
    <DetailsRow name="MAC Address" />
    <DetailsRow :value="device?.uptime" :formatFunc="formatTime" name="Uptime" />
  </el-card>
</template>
