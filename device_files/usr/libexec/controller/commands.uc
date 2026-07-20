'use strict';

import { connect } from 'ubus';
import * as uloop from 'uloop';

import { provision } from 'provision';

const ubus = connect();

export function handle_command(command) {
    switch (command) {
        case "noop":
            break;
        case "reboot":
            ubus.call("system", "reboot");
            break;
        case "provision":
            provision();
            break;
        case "update-inform":
            uloop.process("update_inform", [], null, () => {
                print("updated inform functionality");
            });
            break;
        default:
            print("received " + command + "\n");
            break;
    }
};