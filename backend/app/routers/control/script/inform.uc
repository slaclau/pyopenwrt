'use strict';

let ubus = require('ubus').connect();
let uci = require('uci').cursor();

function call(command, params) {
  return ubus.call("file", "exec", {
    command,
    params,
  }).stdout
}

let inform_ip = "192.168.122.1";
let ip_rtn = call("ip", ["route", "get", inform_ip]);
ip_rtn = split(ip_rtn, " ");
let src_idx = index(ip_rtn, "src");
let management_network = uci.get_first('controller', 'inform', 'management_network');
let management_ip = ubus.call("network.interface." + management_network, "status")?.["ipv4-address"]?.[0]?.address;
if (!management_ip) management_ip = ip_rtn[src_idx + 1];

let iwinfo_devices = ubus.call("iwinfo", "devices");

let device_id = uci.get_first('controller', 'inform', 'device_id');

let ports = {};
for (let port in ubus.call("luci", "getBuiltinEthernetPorts").result) {
  ports[port.device] = port.role;
}

let radios = ubus.call("luci-rpc", "getWirelessDevices");
if (!radios) radios = {};

const rtn = {
  device_id: device_id ? device_id : null,
  ip: management_ip,
  boot_time: trim(call("uptime", ["-s"])),
  model: ubus.call("system", "board").model,
  iwinfo: map(iwinfo_devices.devices, function(device) {
    return {
      device: device,
      assoclist: ubus.call("iwinfo", "assoclist", {"device": device}).results,
    }
  }),
  ports: ports,
  dhcp_leases: ubus.call("luci-rpc", "getDHCPLeases").dhcp_leases,
  radios: radios,
};
print(rtn);
return rtn