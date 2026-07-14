<script setup lang="ts">
import { client } from '@/client'
import {
  getHostLastHourStatsNetifyStatsByHostLastDayGet,
  getApplicationsMapNetifyApplicationsGet,
} from '@/sdk'
import {
  mdiFacebook,
  mdiFirefox,
  mdiGoogle,
  mdiGoogleAds,
  mdiHelp,
  mdiLockOffOutline,
  mdiLockOutline,
  mdiServerOutline,
  mdiTwitter,
  mdiWikipedia,
  mdiYoutube,
} from '@mdi/js'
import { onMounted, onUnmounted, ref } from 'vue'
import { siFastly, siGithub, siSpotify, siWhatsapp, siIcloud, siItunes, siGmail, siAkamai, siGoogle, siApple, siReddit } from 'simple-icons'
import SvgIcon from '@jamescoyle/vue-icon'

let timer
let dpi_data = ref({})
const hostsMode = ref(false)

function formatBytes(bytes) {
  if (bytes < 1000) return `${bytes} B`
  if (bytes < 1000 ** 2) return `${(bytes / 1000).toFixed(0)} KB`
  if (bytes < 1000 ** 3) return `${(bytes / 1000 ** 2).toFixed(1)} MB`
  return `${(bytes / 1000 ** 3).toFixed(2)} GB`
}

function getApplicationName(application, protocol) {
  if (application === 'Unknown') return protocol
  if (application in applications_map) return applications_map[application]
  if (application.includes('netify.'))
    return application
      .replace('netify.', '')
      .replace('-', ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.substring(1))
      .join(' ')
  return application
}

let networkManagementIcon = mdiServerOutline

const application_icons_map = {
  'netify.firefox': mdiFirefox,
  'netify.youtube': mdiYoutube,
  'netify.wikipedia': mdiWikipedia,
  'netify.facebook': mdiFacebook,
  'netify.google-ads': mdiGoogleAds,
  'netify.google-authentication': mdiGoogle,
  'netify.reverse-dns': networkManagementIcon,
  'netify.fastly': siFastly.path,
  'netify.github': siGithub.path,
  'netify.ntp': networkManagementIcon,
  'netify.spotify': siSpotify.path,
  'netify.apple-icloud': siIcloud.path,
  'netify.icloud-private-relay': siIcloud.path,
  'netify.twitter': mdiTwitter,
  'netify.apple-itunes': siItunes.path,
  'netify.gmail': siGmail.path,
  'netify.akamai': siAkamai.path,
  'netify.gsuite': siGoogle.path,
  'netify.apple-mail': siApple.path,
  'netify.reddit': siReddit.path,

}
const protocol_icons_map = {
  HTTP: mdiLockOffOutline,
  'HTTP/S': mdiLockOutline,
  QUIC: mdiLockOutline,
  DHCP: networkManagementIcon,
  IGMP: networkManagementIcon,
  IGMPv6: networkManagementIcon,
  ICMP: networkManagementIcon,
  ICMPv6: networkManagementIcon,
  DNS: networkManagementIcon,
  WhatsApp: siWhatsapp.path,
}

function getAppplicationIcon(application, protocol) {
  if (application === 'Unknown') {
    if (protocol in protocol_icons_map) return protocol_icons_map[protocol]
  }
  if (application in application_icons_map) return application_icons_map[application]
  return mdiHelp
}

let applications_map
getApplicationsMapNetifyApplicationsGet({ client }).then((res) => {
  applications_map = res.data
})

onMounted(() => {
  getHostLastHourStatsNetifyStatsByHostLastDayGet({ client }).then((res) => {
    if (res.data) {
      dpi_data.value = res.data
    } else {
      console.log('no data yet')
    }
  })
  timer = setInterval(() => {
    getHostLastHourStatsNetifyStatsByHostLastDayGet({ client }).then((res) => {
      if (res.data) {
        dpi_data.value = res.data
      } else {
        console.log('no data yet')
      }
    })
  }, 3000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<template>
      <el-radio-group v-model="hostsMode">
        <el-radio-button :value="false">Applications</el-radio-button>
        <el-radio-button :value="true">Hosts</el-radio-button>
      </el-radio-group>

      <el-table v-if="hostsMode" table-layout="auto" :data="dpi_data.hosts?.filter((host) => host.download + host.upload)">
        <el-table-column label="Host">
          <template #default="scope"> {{ scope.row.mac }} / {{ scope.row.ip }} </template>
        </el-table-column>
        <el-table-column label="Data">
          <template #default="scope">
            {{ formatBytes(scope.row.upload) }} / {{ formatBytes(scope.row.download) }}
          </template>
        </el-table-column>
      </el-table>
      <el-table v-else table-layout="auto" :data="dpi_data.categories?.filter((cat) => cat.download + cat.upload)">
        <el-table-column :width="40">
          <template #default="scope">
            <SvgIcon
              type="mdi"
              :path="getAppplicationIcon(scope.row.application, scope.row.protocol)"
              :size="24"
            />
          </template>
        </el-table-column>
        <el-table-column label="Application">
          <template #default="scope">
            {{ getApplicationName(scope.row.application, scope.row.protocol) }}
          </template>
        </el-table-column>
        <el-table-column label="Data">
          <template #default="scope">
            {{ formatBytes(scope.row.upload) }} / {{ formatBytes(scope.row.download) }}
          </template>
        </el-table-column>
      </el-table>
</template>
