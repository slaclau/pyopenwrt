<script setup lang="ts">
import { site_manager_client } from '@/client';
import { getAllMySitesSitesGet, type Site } from '@/sdk';

import { onMounted, ref, type Ref } from 'vue';

const sites: Ref<Site[]> = ref([])


onMounted(() => {
    console.log("mounted");

    getAllMySitesSitesGet({ client: site_manager_client }).then((res) => {
        if (res.data)
            sites.value = res.data;
        console.log("sites", sites.value)
    })
})

</script>

<template>
    <div v-for="site in sites">
        {{ site }}
    </div>
</template>