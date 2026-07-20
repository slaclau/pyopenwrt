'use strict';

import { cursor } from 'uci'; // Direct C-bindings to OpenWrt UCI configurations


export function load_uci_settings() {
    let uci = cursor();
    let config = {};

    // Map UCI defaults with hard fallback safety values
    config.controller_ip = uci.get_first("controller", "inform", "controller_ip") || "127.0.0.1";
    config.stun_port = int(uci.get_first("controller", "stun", "stun_port") || 3478);
    config.stun_interval = int(uci.get_first("controller", "stun", "stun_interval") || 25000);
    config.inform_interval = int(uci.get_first("controller", "inform", "inform_interval") || 20000);
    config.device_id = uci.get_first("controller", "inform", "device_id");

    return config;
};