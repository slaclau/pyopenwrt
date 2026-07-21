<script setup lang="ts">
import {
  getDeviceConfigurationDevicesDeviceIdGet,
  provisionControlProvisionDeviceIdPost,
  updateDeviceConfigurationDevicesDeviceIdPut,
  type DeviceStatusWithDevice
} from 'controller/sdk'
import { client } from '@/client'

const props = defineProps<{
  device: DeviceStatusWithDevice | undefined
}>()

function onSubmit(): void {
  if (props.device === undefined) return
  if (props.device.device !== null) {
    if (props.device.device.address_proto === 'dhcp') props.device.device.address = null
    updateDeviceConfigurationDevicesDeviceIdPut({
      client,
      path: {
        device_id: props.device.device.device_id,
      },
      body: props.device.device,
    }).then(() => {
      if (props.device === undefined) return
      console.log(`updated device ${props.device.device?.device_id}`)
      provisionControlProvisionDeviceIdPost({
        client,
        path: { device_id: props.device.device.device_id },
      }).then(() => {
        console.log('provisioning device')
      })
    })
  }
}

function onCancel(): void {
  if (props.device === undefined) return
  getDeviceConfigurationDevicesDeviceIdGet({
    client,
    path: { device_id: props.device.device_id },
  }).then((res) => {
    if (props.device === undefined) return
    if (res.data !== undefined) props.device.device = res.data
  })
}
</script>

<template>
  <el-form v-if="device" label-width="auto">
    <el-form-item>
      <el-button @click="onCancel">Cancel</el-button>
      <el-button type="primary" @click="onSubmit">Update</el-button>
    </el-form-item>
    <el-card>
      <el-form-item label="Hostname">
        <el-input v-model="device.device.hostname" />
      </el-form-item>
      <el-form-item label="IP Address Type">
        <el-radio-group v-model="device.device.address_proto">
          <el-radio value="dhcp">DHCP</el-radio>
          <el-radio value="static">Static</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item>
        <el-input v-model="device.device.address" :disabled="device.device.address_proto === 'dhcp' ? true : false" />
      </el-form-item>
    </el-card>
  </el-form>
</template>
