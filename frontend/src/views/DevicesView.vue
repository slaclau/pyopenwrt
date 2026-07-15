<script setup lang="ts">
import { onMounted, ref, type Ref } from 'vue'

import DeviceComponent from '@/components/devices/DeviceDrawerComponent.vue'
import type { DeviceStatusWithDevice } from '@/sdk'
import DeviceIcon from '@/components/devices/DeviceIcon.vue'
import { formatTime } from '@/utils'

const selectedDevice: Ref<DeviceStatusWithDevice | undefined> = ref(undefined)
const openDrawer = ref(false)
let drawerWidth: Ref<string>

defineProps<{
  devices: Array<DeviceStatusWithDevice> | undefined
}>()

onMounted(() => {
  drawerWidth = ref(window.screen.width < 500 ? '100%' : '30%')
})

function selectDevice(row: DeviceStatusWithDevice) {
  selectedDevice.value = row
  openDrawer.value = true
}
</script>

<template>
  <div>
    <el-table :data="devices" style="width: 100%" table-layout="auto" @row-click="selectDevice">
      <el-table-column width="100">
        <template #default="scope">
          <DeviceIcon :device="scope.row.device" />
        </template>
      </el-table-column>
      <el-table-column prop="device.hostname" label="Hostname" />
      <el-table-column prop="last_ip" label="IP Address" />
      <el-table-column>
        <template #default="scope">
          {{
            scope.row.device.adopted
              ? scope.row.up
                ? '✔ for ' + formatTime(scope.row.uptime)
                : scope.row.time_since_inform
                  ? '✗ for ' + formatTime(scope.row.time_since_inform)
                  : '✗'
              : 'Awaiting adoption'
          }}
        </template>
      </el-table-column>
    </el-table>
  </div>
  <el-drawer v-model="openDrawer" :size="drawerWidth">
    <DeviceComponent :device="selectedDevice" />
  </el-drawer>
</template>
