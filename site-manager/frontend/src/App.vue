<script setup lang="ts">
import { onMounted, ref, type Ref } from 'vue';

import { mdiArrowLeft, mdiThemeLightDark } from '@mdi/js';
import { useDark, useToggle } from '@vueuse/core';

import SvgIcon from '@jamescoyle/vue-icon'
import router from './router';


const isDark = useDark()
const toggleDark = useToggle(isDark)

onMounted(() => {
  console.log("mounted");
})
</script>

<template>
  <el-container>
    <el-header>
      <h1>
        <span style="float: left"><el-button @click="router.back()"><svg-icon type="mdi" :path="mdiArrowLeft"
              :size="24" /></el-button></span>
        OpenWrt Site Manager
        <span style="float: right"><el-button @click="toggleDark()"><svg-icon type="mdi" :path="mdiThemeLightDark"
              :size="24" /></el-button></span>
      </h1>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped></style>
