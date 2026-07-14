import type { DeviceRole } from './sdk/types.gen'
import { mdiRouterNetworkWireless, mdiRouterNetwork, mdiAccessPointNetwork, mdiLan } from '@mdi/js'

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

  var rtn = ''
  if (days) rtn += `${days}d `
  if (hours) rtn += `${hours}h `
  if (minutes) rtn += `${minutes}m `
  rtn += `${outSeconds}s`
  return rtn
}
