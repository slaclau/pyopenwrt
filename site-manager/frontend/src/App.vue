<script setup lang="ts">
import { mdiArrowLeft, mdiThemeLightDark } from '@mdi/js';
import { useDark, useToggle } from '@vueuse/core';

import SvgIcon from '@jamescoyle/vue-icon'
import router from './router';


const isDark = useDark()
const toggleDark = useToggle(isDark)

import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <el-container>
    <el-header>
      <h1>
        <span style="float: left"><el-button :style="`visibility: ${['/', '/login'].includes(route.path) ? 'hidden'
          : 'visible'}`" @click="router.back()">
            <svg-icon type="mdi" :path="mdiArrowLeft" :size="24" />
          </el-button>
        </span>
        <span class="header-title">Site Manager</span>
        <span style="float: right">
          <el-button @click="toggleDark()">
            <svg-icon type="mdi" :path="mdiThemeLightDark" :size="24" />
          </el-button>
        </span>
      </h1>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.header-title {
  margin-left: 16px;
  /* Creates the gap between left button and title */
}
</style>
