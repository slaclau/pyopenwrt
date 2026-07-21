<script setup lang="ts">
import {
  getNetworkConfigurationNetworksNetworkIdGet,
  updateNetworkConfigurationNetworksNetworkIdPut,
  provisionAllControlProvisionPost,
  type NetworkInput,
  type NetworkOutput,
  createNetworkConfigurationNetworksPost,
} from 'controller/sdk'
import { client } from '@/client'
import { ref, type Ref } from 'vue'

const props = defineProps<{
  network: NetworkOutput | null
}>()

const config: Ref<NetworkInput | null> = ref(props.network)

function onSubmit(): void {
  if (!config.value) return
  if (!config.value?.network_id) {
    config.value.network_id = config.value.name.toLowerCase().replace(' ', '').slice(0, 5)
    config.value.management = false
    console.log(`created network ${config.value?.network_id}`)
    createNetworkConfigurationNetworksPost({
      client,
      body: config.value,
    }).then(() => {
      provisionAllControlProvisionPost({ client }).then(() => {
        console.log('provisioning all devices')
      })
    })
  } else {
    updateNetworkConfigurationNetworksNetworkIdPut({
      client,
      path: {
        network_id: config.value.network_id,
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
  getNetworkConfigurationNetworksNetworkIdGet({
    client,
    path: { network_id: config.value?.network_id },
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
      <el-form-item label="Name">
        <el-input v-model="config.name" />
      </el-form-item>
      <el-form-item label="VLAN ID">
        <el-input v-model="config.vlan_id" />
      </el-form-item>
    </el-card>
    <el-card>
      <el-form-item label="Gateway IP">
        <el-input v-model="config.gateway_ip" />
      </el-form-item>
      <el-form-item label="Subnet Mask">
        <el-input-number :min="0" :max="32" v-model="config.subnet_mask" />
      </el-form-item>
    </el-card>
    <el-card>
      <el-form-item label="DHCP Range">
        <el-col :span="11">
          <el-input v-model="config.dhcp_start_ip" style="width: 100%" />
        </el-col>
        <el-col :span="2" style="text-align: center">
          <span class="text-gray-500"> - </span>
        </el-col>
        <el-col :span="11">
          <el-input v-model="config.dhcp_end_ip" style="width: 100%" />
        </el-col>
      </el-form-item>
    </el-card>
  </el-form>
</template>
