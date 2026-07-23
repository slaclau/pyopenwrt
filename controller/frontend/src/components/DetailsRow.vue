/* eslint-disable @typescript-eslint/no-explicit-any */
<script setup lang="ts" generic="T">

const props = defineProps<{ value?: T, name?: string, formatFunc?: (value: T) => string }>()


function format(val: T) {
  if (props.formatFunc) return props.formatFunc(val)
  return val
}
</script>

<template>
  <div>
    <small>
      <span>{{ name }}</span> <span style="float: right">{{ value ? format(value) : "" }}</span>
    </small>
  </div>
</template>
