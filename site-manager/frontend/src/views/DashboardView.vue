<script setup lang="ts">
import { site_manager_client } from '@/client';
import SiteTile from '@/components/SiteTile.vue';
import { setIntervalImmediate } from '@/controller_src/utils';
import { getAllMySitesSitesGet, type Site } from '@/sdk';
import router from '@/router'
import { onMounted, onUnmounted, ref, type Ref } from 'vue';

const sites: Ref<Site[]> = ref([])
let timer: number;

onMounted(() => {
    timer = setIntervalImmediate(() => {
        getAllMySitesSitesGet({ client: site_manager_client }).then((res) => {
            if (res.data)
                sites.value = res.data;
        })
    }, 3000)
})

onUnmounted(() => {
    clearInterval(timer)
})

</script>

<template>
    <div v-for="site in sites">
        <el-row>
            <el-col :xs="24" :sm="12" :md="6" :lg="4" :xl="3">
                <SiteTile :site="site" @click="router.push(`/sites/${site.site_id}`)" shadow="hover" />
            </el-col>
        </el-row>
    </div>
</template>