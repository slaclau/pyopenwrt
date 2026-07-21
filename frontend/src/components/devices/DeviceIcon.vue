<script setup lang="ts">
import { makeIcon } from 'controller/utils'
import SvgIcon from '@jamescoyle/vue-icon'
import { type Device } from 'controller/sdk'

defineProps<{
  device: Device | undefined
}>()
</script>

<template>
  <svg-icon type="mdi" :path="makeIcon(device?.roles)" :size="24" />
</template>
