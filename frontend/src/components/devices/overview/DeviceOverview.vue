<script setup lang="ts">

import { adoptControlAdoptDeviceIdPost, type DeviceStatusWithDevice } from 'controller/sdk'
import DeviceDetails from 'controller/components/devices/overview/DeviceDetails.vue'
import DeviceSummary from 'controller/components/devices/overview/DeviceSummary.vue'
import { client } from '@/client.ts'

const props = defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()

function adopt() {
  if (props.device) {
    adoptControlAdoptDeviceIdPost({ client, path: { device_id: props.device.device_id } }).then(
      () => {
        console.log(`adopted ${props.device?.device_id}`)
      },
    )
  }
}
</script>

<template>
  <DeviceSummary :device="device" />
  <DeviceDetails :device="device" />
  <el-button><a download :href="`${window.origin}/api/configuration/raw/${device?.device_id}`">Download
      Configuration</a></el-button>
  <el-button v-if="!device?.device.adopted" @click="adopt">Adopt</el-button>
</template>
