#!/usr/bin/ucode

import { create as create_socket, AF_INET, SOCK_DGRAM, SOCK_NONBLOCK } from 'socket';
import { stdout } from "fs";
import * as math from 'math';
import * as uloop from 'uloop';
import * as uclient from 'uclient';
import { connect } from 'ubus';

import { get_payload as get_inform_payload } from 'inform';
import { handle_command } from 'commands';
import { load_uci_settings } from 'settings';

uloop.init();

ubus = connect();

let nat_ip;
let nat_port;

// Load configurations immediately on cold boot execution
config = load_uci_settings();


function handle_inform_response(res) {
    if (!res) {
        warn("no response to inform\n");
        return;
    }
    command = res.command;
    handle_command(command);
}

function send_inform() {
    print("sending inform\n");
    let status_payload = get_inform_payload();
    status_payload.nat = { "nat_ip": nat_ip, "nat_port": nat_port };
    let json_string = sprintf("%J", status_payload);
    url = "http://" + config.controller_ip + ":8000/control/inform";

    uc = uclient.new(url, null, {
        data_read: (cb) => {
            let res = json(uc);
            handle_inform_response(res);
        },
        data_eof: (cb) => {
            stdout.flush();
        },
        error: (cb, code) => {
            warn(`Error: ${code}\n`);
        },
    });

    if (!uc.connect()) {
        warn(`Failed to connect\n`);
    } else {
        if (!uc.request("POST", {
            post_data: json_string,
            headers: { "Content-Type": "application/json" },
        })) {
            warn(`Failed to send request\n`);
        }
    }
}

const sock = create_socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK);
if (!sock) { print("FATAL: Socket creation error\n"); exit(1); }

function build_stun_packet() {
    let tx_id = [];
    for (let i = 0; i < 12; i++) { tx_id[i] = int(math.rand() * 256); }
    return [0x00, 0x01, 0x00, 0x00, 0x21, 0x12, 0xA4, 0x42, ...tx_id];
}

let stun_timer;
function send_stun_keepalive() {
    print("sending stun binding request\n");
    let packet_bytes = build_stun_packet();
    let binary_payload = join("", map(packet_bytes, b => chr(b)));

    sock.send(binary_payload, 0, config.controller_ip + ":" + config.stun_port); // Pulls dynamic target state

    stun_timer.set(config.stun_interval); // Pulls dynamic refresh intervals
}
stun_timer = uloop.timer(-1, send_stun_keepalive);
stun_timer.set(config.stun_interval);

let inform_timer;
function send_periodic_inform() {
    send_inform();
    inform_timer.set(config.inform_interval);
}
inform_timer = uloop.timer(-1, send_periodic_inform);
inform_timer.set(config.inform_interval);

function handle_socket_events(events) {
    let incoming = sock.recv();
    if (!incoming) return;
    let payload = incoming;

    if (length(payload) >= 20 && (ord(payload, 0) & 0b11000000) == 0) {
        switch (ord(payload, 0)) {
            case 0x01:
                switch (ord(payload, 1)) {
                    case 0x01:
                        let attributes_length = ord(payload, 2) * 256 + ord(payload, 3);
                        let offset = 0;
                        while (offset < attributes_length) {
                            l = ord(payload, 20 + offset + 2) * 256 + ord(payload, 20 + offset + 3);

                            if (ord(payload, 20 + offset) != 0) {
                                warn("unknown attr id", ord(payload, 20 + offset), ord(payload, 20 + offset + 1), "\n");
                            }
                            let attr = substr(payload, 20 + offset + 4, l);
                            switch (ord(payload, 20 + offset + 1)) {
                                case 1:
                                    if (ord(attr, 1) != 1) {
                                        warn("invalid ip family in stun mapped address");
                                    }
                                    port = ord(attr, 2) * 256 + ord(attr, 3);
                                    ip = arrtoip([ord(attr, 4), ord(attr, 5), ord(attr, 6), ord(attr, 7)]);

                                    if (port != nat_port && ip != nat_ip) {
                                        printf("got updated nat address %s:%d\n", ip, port);
                                        nat_port = port;
                                        nat_ip = ip;
                                        send_inform();
                                    }
                                    break;
                                default:
                                    warn("unknown attr id", ord(payload, 20 + offset), ord(payload, 20 + offset + 1), "\n");
                                    break;
                            }


                            offset += l + 4;
                        }

                        break;
                    default:
                        warn("got unexpected stun response\n");
                        break;
                }
                break;
            case 0x00:
                warn("got unexpected stun request\n");
                break;
        }

        return;
    }
    command = trim(payload);
    handle_command(command);
}


uloop.handle(sock, handle_socket_events, uloop.ULOOP_READ);



send_stun_keepalive();
send_inform();


uloop.run();
