'use strict';
import { stdout, open } from "fs";

import * as uclient from 'uclient';
import * as uloop from 'uloop';
import { connect } from 'ubus';

import { load_uci_settings } from 'settings';

const ubus = connect();

function load_new_config(path) {
    print("loading new config from " + path + "\n");
    uloop.process("sysupgrade", ["-r", path], null, () => {

        print("reloading services\n");

        let services = ["system", "wireless", "network", "dnsmasq", "controller"];

        for (let service in services) {
            print("  reloading " + service + "\n");
            ubus.call("rc", "init", { "name": service, "action": "reload" });
        }
        print("done\n");
    });
};

export function provision() {
    print("provisioning\n");
    config = load_uci_settings();
    url = "http://" + config.controller_ip + ":8000/configuration/raw/" + config.device_id;
    print("downloading config from " + url + "\n");
    let path = "/tmp/new.tar.gz";
    let file = open(path, "w");

    uc = uclient.new(url, null, {
        data_read: (cb) => {
            file.write(uc.read());
        },
        data_eof: (cb) => {
            if (!file.close()) {
                print("could not write new config to tmp file\n");
            }
            print("new config written to " + path + "\n");
            load_new_config(path);
        },
        error: (cb, code) => {
            warn(`Error: ${code}\n`);
        },
    });

    if (!uc.connect()) {
        warn(`Failed to connect\n`);
    }

    if (!uc.request("GET")) {
        warn(`Failed to send request\n`);
    }
};
