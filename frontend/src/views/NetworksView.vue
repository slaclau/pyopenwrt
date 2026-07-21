<script setup lang="ts">
import { getAllNetworksConfigurationNetworksGet, type NetworkOutput, type NetworkStatus, type Status } from 'controller/sdk'
import { client } from '@/client'
import { ref, type Ref } from 'vue'

import NetworkDrawerComponent from 'controller/components/settings/networks/NetworkDrawerComponent.vue'

const networks: Ref<Array<NetworkOutput> | undefined> = ref([])
getAllNetworksConfigurationNetworksGet({ client }).then((res) => {
  networks.value = res.data
  console.log(networks)
})

const selectedNetwork: Ref<NetworkOutput | null> = ref(null)
const openDrawer = ref(false)
const drawerWidth = ref(window.screen.width < 500 ? '100%' : '30%')

function selectNetwork(row: NetworkStatus) {
  selectedNetwork.value = row.network
  openDrawer.value = true
}
function addNetwork() {
  selectedNetwork.value = null
  openDrawer.value = true
}
// function getIPLeases(network_id: string, dhcp_server_id: string) {
//   return props.status?.network_status?.filter(
//     (network) => network.network.dhcp_server_id == dhcp_server_id,
//   )[0].dhcp_leases
// }
defineProps<{
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
