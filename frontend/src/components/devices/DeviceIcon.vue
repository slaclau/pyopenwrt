<script setup lang="ts">
import { makeIcon } from '@/utils'
import SvgIcon from '@jamescoyle/vue-icon'
import { type Device } from '@/sdk'

defineProps<{
  device: Device | undefined
}>()
</script>

<template>
  <svg-icon type="mdi" :path="makeIcon(device?.roles)" :size="24" />
</template>
