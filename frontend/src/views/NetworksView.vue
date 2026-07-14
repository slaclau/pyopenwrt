<script setup lang="ts">
import { getAllNetworksConfigurationNetworksGet, type NetworkOutput, type Status } from '@/sdk'
import { client } from '../client'
import { ref, type Ref } from 'vue'

import NetworkDrawerComponent from '@/components/settings/networks/NetworkDrawerComponent.vue'

let networks: Ref<Array<NetworkOutput> | undefined> = ref([])
getAllNetworksConfigurationNetworksGet({ client }).then((res) => {
  networks.value = res.data
  console.log(networks)
})

let selectedNetwork: Ref<NetworkOutput | null> = ref(null)
let openDrawer = ref(false)
let drawerWidth = ref(window.screen.width < 500 ? '100%' : '30%')

function selectNetwork(row: any, column: any, event: any) {
  selectedNetwork.value = row.network
  openDrawer.value = true
}
function addNetwork() {
  selectedNetwork.value = null
  openDrawer.value = true
}
function getIPLeases(network_id: String, dhcp_server_id: String) {
  return props.status?.network_status?.filter(
    (network) => network.network.dhcp_server_id == dhcp_server_id,
  )[0].dhcp_leases
}
const props = defineProps<{
  status: Status | null
}>()
</script>

<template>
  <el-table v-if="status" :data="status.network_status" table-layout="auto" @row-click="selectNetwork">
    <el-table-column prop="network.name" label="Name" />
    <el-table-column prop="network.vlan_id" label="VLAN ID" />
    <el-table-column prop="network.router.hostname" label="Router" />
    <el-table-column prop="network.network_address" label="Subnet" />
    <el-table-column prop="network.dhcp_server.hostname" label="DHCP" />
    <el-table-column label="IP Leases">
      <template #default="scope">
        {{ scope.row.dhcp_leases.length }}
      </template>
    </el-table-column>
    <el-table-column prop="network.dhcp_pool_size" label="Pool Size" />
    <el-table-column label="Available">
      <template #default="scope">
        {{ scope.row.network.dhcp_pool_size - scope.row.dhcp_leases.length }}
      </template>
    </el-table-column>
    <el-table-column label="Range">
      <template #default="scope">
        {{ scope.row.network.dhcp_start_ip }} - {{ scope.row.network.dhcp_end_ip }}
      </template>
    </el-table-column>
  </el-table>
  <el-button type="primary" @click="addNetwork">Add Network</el-button>
  <el-drawer v-model="openDrawer" :size="drawerWidth">
    <NetworkDrawerComponent :network="selectedNetwork" />
  </el-drawer>
</template>
