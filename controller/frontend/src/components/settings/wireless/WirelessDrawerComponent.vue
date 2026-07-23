<script setup lang="ts">
import {
  createWirelessNetworkConfigurationWirelessPost,
  getWirelessNetworkConfigurationWirelessWirelessIdGet,
  provisionAllControlProvisionPost,
  updateWirelessNetworkConfigurationWirelessWirelessIdPut,
  type Wireless,
} from 'controller/sdk'
import { client } from '@/client'
import { ref, type Ref } from 'vue'

const props = defineProps<{
  network: Wireless | null
}>()

const config: Ref<Wireless | null> = ref(props.network)

function onSubmit(): void {
  if (!config.value) return
  if (!config.value?.wireless_id) {
    config.value.wireless_id = config.value.ssid.toLowerCase().replace(' ', '').slice(0, 5)
    console.log(`created network ${config.value?.network_id}`)
    createWirelessNetworkConfigurationWirelessPost({
      client,
      body: config.value,
    }).then(() => {
      provisionAllControlProvisionPost({ client }).then(() => {
        console.log('provisioning all devices')
      })
    })
  } else {
    updateWirelessNetworkConfigurationWirelessWirelessIdPut({
      client,
      path: {
        wireless_id: config.value.wireless_id,
      },
      body: config.value,
    }).then(() => {
      console.log(`updated network ${config.value?.network_id}`)
      provisionAllControlProvisionPost({ client }).then(() => {
        console.log('provisioning all devices')
      })
    })
  }
}

function onCancel(): void {
  getWirelessNetworkConfigurationWirelessWirelessIdGet({
    client,
    path: { wireless_id: config.value?.wireless_id },
  }).then((res) => {
    if (res.data !== undefined) config.value = res.data
  })
}
</script>

<template>
  <el-form label-width="auto" v-if="config">
    <el-form-item>
      <el-button @click="onCancel">Cancel</el-button>
      <el-button type="primary" @click="onSubmit">Update</el-button>
    </el-form-item>
    <el-card>
      <el-form-item label="SSID">
        <el-input v-model="config.ssid" />
      </el-form-item>
    </el-card>
  </el-form>
</template>
