<script setup lang="ts">
import type { Site } from '@/sdk';
import StatusDot from './StatusDot.vue'
defineProps<{ site: Site }>();

</script>

<template>
    <el-card>
        <template #header>
            <div class="card-header">
                {{ site.name }}
            </div>
        </template>
        <div>
            <StatusDot :online="site.up" />
        </div>
    </el-card>
</template>