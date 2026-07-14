<script setup lang="ts">
import { getAllWirelessNetworksConfigurationWirelessGet, type Wireless, type Status } from '@/sdk'
import { client } from '../client'
import { ref, type Ref } from 'vue'

import WirelessDrawerComponent from '@/components/settings/wireless/WirelessDrawerComponent.vue'

let networks: Ref<Array<Wireless> | undefined> = ref([])
getAllWirelessNetworksConfigurationWirelessGet({ client }).then((res) => {
  networks.value = res.data
  console.log(networks)
})

let selectedNetwork: Ref<Wireless | null> = ref(null)
let openDrawer = ref(false)
let drawerWidth = ref(window.screen.width < 500 ? '100%' : '30%')

function selectNetwork(row: any, column: any, event: any) {
  selectedNetwork.value = row
  openDrawer.value = true
}
function addNetwork() {
  selectedNetwork.value = null
  openDrawer.value = true
}
const props = defineProps<{
  status: Status | null
}>()
</script>

<template>
  <el-table v-if="status" :data="networks" table-layout="auto" @row-click="selectNetwork">
    <el-table-column prop="ssid" label="SSID" />
    <el-table-column prop="network_id" label="Network" />
  </el-table>
  <el-button type="primary" @click="addNetwork">Add Network</el-button>
  <el-drawer v-model="openDrawer" :size="drawerWidth">
    <WirelessDrawerComponent :network="selectedNetwork" />
  </el-drawer>
</template>
