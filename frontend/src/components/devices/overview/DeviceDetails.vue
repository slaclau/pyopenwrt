<script setup lang="ts">
import type { DeviceStatusWithDevice } from '../../../sdk/types.gen'
import { formatTime } from '../../../utils'
import DetailsRow from '../../DetailsRow.vue'
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
