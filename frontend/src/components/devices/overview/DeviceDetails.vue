<script setup lang="ts">
import type { Ref } from 'vue'
import type { DeviceStatusWithDevice } from '../../../sdk/types.gen'
import { formatTime } from '../../../utils'
import Row from '../../Row.vue'
const props = defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()
</script>

<template>
  <el-card>
    <Row :value="device?.device.model" name="Model" />
    <Row :value="device?.last_ip" name="IP Address" />
    <Row name="MAC Address" />
    <Row :value="device?.uptime" :formatFunc="formatTime" name="Uptime" />
  </el-card>
</template>
