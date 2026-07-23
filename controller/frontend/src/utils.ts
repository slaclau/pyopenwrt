import type { DeviceRole } from 'controller/sdk/types.gen'
import { mdiRouterNetworkWireless, mdiRouterNetwork, mdiAccessPointNetwork, mdiLan } from '@mdi/js'
import { getApplicationsMapNetifyApplicationsGet } from 'controller/sdk'
import { client } from '@/client'

export function makeIcon(roles: Array<DeviceRole> | undefined) {
  if (roles === undefined) return
  if (roles.includes('router')) {
    if (roles.includes('ap')) return mdiRouterNetworkWireless
    return mdiRouterNetwork
  }
  if (roles.includes('ap')) return mdiAccessPointNetwork
  return mdiLan
}

export function formatTime(seconds: number) {
  const days = Math.floor(seconds / (3600 * 24))
  const hours = Math.floor((seconds - 3600 * 24 * days) / 3600)
  const minutes = Math.floor((seconds - 3600 * 24 * days - 3600 * hours) / 60)
  const outSeconds = Math.round(seconds - 3600 * 24 * days - 3600 * hours - 60 * minutes)

  let rtn = ''
  if (days) rtn += `${days}d `
  if (hours) rtn += `${hours}h `
  if (minutes) rtn += `${minutes}m `
  rtn += `${outSeconds}s`
  return rtn
}

let applications_map: { [key: string]: string }

function getApplicationNameInner(arg: string) {
  if (arg in applications_map) { return applications_map[arg] }
  else if (arg.includes('netify.')) {
    return arg
      .replace('netify.', '')
      .replace('-', ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.substring(1))
      .join(' ')
  } else {
    return arg
  }
}

export function getApplicationName(application: string, protocol: string) {
  if (application === 'Unknown') return protocol


  if (!applications_map) {
    getApplicationsMapNetifyApplicationsGet({ client }).then((res) => {
      if (res.data) {
        applications_map = res.data;
        return getApplicationNameInner(application)
      } else {
        return application
          .replace('netify.', '')
          .replace('-', ' ')
          .split(' ')
          .map((word) => word.charAt(0).toUpperCase() + word.substring(1))
          .join(' ')
      }
    })
  } else {
    return getApplicationNameInner(application)
  }



}

const networkManagementIcon = mdiServerOutline

const application_icons_map: { [key: string]: string } = {
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
const protocol_icons_map: { [key: string]: string } = {
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

import {
  siFastly,
  siGithub,
  siSpotify,
  siWhatsapp,
  siIcloud,
  siItunes,
  siGmail,
  siAkamai,
  siGoogle,
  siApple,
  siReddit,
} from 'simple-icons'

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

export function getAppplicationIcon(application: string, protocol: string) {
  if (application === 'Unknown') {
    if (protocol in protocol_icons_map) return protocol_icons_map[protocol]
  }
  if (application in application_icons_map) return application_icons_map[application]
  return mdiHelp
}

export function formatBytes(bytes: number) {
  if (bytes < 1000) return `${bytes} B`
  if (bytes < 1000 ** 2) return `${(bytes / 1000).toFixed(0)} KB`
  if (bytes < 1000 ** 3) return `${(bytes / 1000 ** 2).toFixed(1)} MB`
  return `${(bytes / 1000 ** 3).toFixed(2)} GB`
}

/* eslint-disable @typescript-eslint/no-unsafe-function-type */
export function setIntervalImmediate(func: Function, interval: number): number {
  func()
  return setInterval(func, interval)
}
