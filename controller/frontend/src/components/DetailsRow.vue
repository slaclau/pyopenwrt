/* eslint-disable @typescript-eslint/no-explicit-any */
<script setup lang="ts">

const props = defineProps<{ value?: unknown, name?: string, formatFunc?: (value: unknown) => string }>()


function format(val: unknown) {
  if (props.formatFunc) return props.formatFunc(val)
  return val
}
</script>

<template>
  <div>
    <small>
      <span>{{ name }}</span> <span style="float: right">{{ format(value) }}</span>
    </small>
  </div>
</template>
