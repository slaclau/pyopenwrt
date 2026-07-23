<script setup lang="ts">
import {
  provisionControlProvisionDeviceIdPost,
  rebootControlRebootDeviceIdPost,
  type DeviceStatusWithDevice,
} from 'controller/sdk'
import { client } from '@/client'
const props = defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()

function reboot() {
  if (props.device === undefined) return
  rebootControlRebootDeviceIdPost({
    client,
    path: { device_id: props.device?.device_id },
  }).then((res) => {
    if (res.error) {
      console.log(res)
    }
  })
}

function provison() {
  if (props.device === undefined) return
  provisionControlProvisionDeviceIdPost({
    client,
    path: { device_id: props.device?.device_id },
  }).then((res) => {
    if (res.error) {
      console.log(res)
    }
  })
}
</script>

<template>
  <el-button @click="reboot" type="danger">Reboot</el-button>
  <el-button @click="provison" type="primary">Provision</el-button>
</template>
