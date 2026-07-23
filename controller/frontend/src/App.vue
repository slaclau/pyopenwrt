<script setup lang="ts">
import { client } from '@/client'
import { getStatusStatusGet, type Status } from 'controller/sdk'

import SvgIcon from '@jamescoyle/vue-icon'
import {
  mdiThemeLightDark,
} from '@mdi/js'

import { useDark, useToggle } from '@vueuse/core'
import { onMounted, onUnmounted, ref, type Ref } from 'vue'
import { setIntervalImmediate } from './utils'
import MainView from './views/MainView.vue'

const isDark = useDark()
const toggleDark = useToggle(isDark)

</script>

<template>
  <el-container>
    <el-header>
      <h1>
        OpenWrt Controller
        <span style="float: right"><el-button @click="toggleDark()"><svg-icon type="mdi" :path="mdiThemeLightDark"
              :size="24" /></el-button></span>
      </h1>
    </el-header>
    <MainView />
  </el-container>
</template>
