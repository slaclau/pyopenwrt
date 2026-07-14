<script setup lang="ts">
const props = defineProps(['value', 'name', 'formatFunc'])

function format(val: any) {
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
