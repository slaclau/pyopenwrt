<script setup lang="ts">
defineProps<{ online: boolean }>();
</script>

<template>
    <div id="statusDot" :class="online ? 'online' : 'offline'"></div>
</template>

<style lang="css">
#statusDot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    transition: background-color 0.3s ease;
}

.online {
    background-color: #22c55e;
    /* Green for online */
}

.offline {
    background-color: #ef4444;
    /* Red for offline */
}
</style>