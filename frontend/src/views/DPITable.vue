<script setup lang="ts">
import type { HostTimeStats } from '@/sdk'
import { formatBytes, getAppplicationIcon, getApplicationName } from '@/utils'
import { ref } from 'vue'

defineProps<{
  dpi_data: HostTimeStats | null
}>()

import SvgIcon from '@jamescoyle/vue-icon'

const hostsMode = ref(false)
</script>

<template>
  <el-radio-group v-model="hostsMode">
    <el-radio-button :value="false">Applications</el-radio-button>
    <el-radio-button :value="true">Hosts</el-radio-button>
  </el-radio-group>
  <el-table
    v-if="hostsMode"
    table-layout="auto"
    :data="dpi_data?.hosts?.filter((host) => host.download + host.upload)"
  >
    <el-table-column label="Host">
      <template #default="scope"> {{ scope.row.mac }} / {{ scope.row.ip }} </template>
    </el-table-column>
    <el-table-column label="Data">
      <template #default="scope">
        {{ formatBytes(scope.row.upload) }} / {{ formatBytes(scope.row.download) }}
      </template>
    </el-table-column>
  </el-table>
  <el-table
    v-else
    table-layout="auto"
    :data="dpi_data?.categories?.filter((cat) => cat.download + cat.upload)"
  >
    <el-table-column :width="40">
      <template #default="scope">
        <SvgIcon
          type="mdi"
          :path="getAppplicationIcon(scope.row.application, scope.row.protocol)"
          :size="24"
        />
      </template>
    </el-table-column>
    <el-table-column label="Application">
      <template #default="scope">
        {{ getApplicationName(scope.row.application, scope.row.protocol) }}
      </template>
    </el-table-column>
    <el-table-column label="Data">
      <template #default="scope">
        {{ formatBytes(scope.row.upload) }} / {{ formatBytes(scope.row.download) }}
      </template>
    </el-table-column>
  </el-table>
</template>
