import pathlib
import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse, Response
from netjsonconfig import OpenWrt
from sqlmodel import select


from .internet import Internet
from ...dependencies import SessionDep
from .devices import Device, DeviceRole, AddressProto
from .networks import Network
from .radios import Radio
from .wireless import Wireless

router = APIRouter(prefix="/configuration", tags=["provisioning"])


def make_network_config(device: Device, session: SessionDep):
    networks = session.query(Network).all()
    internets = session.query(Internet).all()

    loopback = {
        "name": "lo",
        "type": "loopback",
        "addresses": [
            {
                "family": "ipv4",
                "proto": "static",
                "address": "127.0.0.1",
                "mask": 8,
            },
        ],
    }
    ports = [port.port_id for port in device.lan_ports]
    bridge = {
        "name": "main",
        "type": "bridge",
        "stp": False,
        "bridge_members": ports,
        "vlan_filtering": [
            {
                "vlan": network.vlan_id,
                "ports": [
                    {
                        "ifname": port,
                        "tagging": "t",
                        "primary_vid": network.management,
                    }
                    for port in ports
                ],
            }
            for network in networks
        ],
    }
    if DeviceRole.AP in device.roles:
        for i, network in enumerate(networks):
            bridge["vlan_filtering"][i]["ports"].append(
                {
                    "ifname": f"bat0.{network.vlan_id}",
                    "tagging": "u",
                    "primary_vid": False,
                }
            )
            bridge["bridge_members"].append(f"bat0.{network.vlan_id}")

    config = [loopback, bridge]

    for network in networks:
        config.append(
            {
                "name": f"br-main.{network.vlan_id}",
                "network": network.network_id,
                "type": "ethernet",
                "addresses": (
                    [
                        {
                            "family": "ipv4",
                            "proto": device.address_proto.value,
                            "address": (
                                str(network.gateway_ip)
                                if network.router_id == device.device_id
                                else device.address if device.address else None
                            ),
                            "mask": network.subnet_mask if device.address else None,
                            "gateway": (
                                str(network.gateway_ip) if device.address else None
                            ),
                            "dns": (
                                network.gateway_ip
                                if device.address_proto == AddressProto.STATIC
                                else ""
                            ),
                        }
                    ]
                    if network.management or network.router_id == device.device_id
                    else []
                ),
            }
        )
    for internet in internets:
        if internet.device_id == device.device_id:
            config.append(
                {
                    "name": internet.name,
                    "network": internet.name.lower(),
                    "type": "other",
                    "device": internet.port_id,
                    "proto": "pppoe",
                }
            )
    if DeviceRole.AP in device.roles:
        config.append(
            {
                "name": "bat0",
                "type": "other",
                "proto": "batadv",
                "routing_algo": "BATMAN_V",
                "bridge_loop_avoidance": 1,
            }
        )
        radios = session.exec(
            select(Radio.radio_id).where(Radio.device_id == device.device_id)
        )

        for radio in radios:
            config.append(
                {
                    "name": f"vwire-{radio}",
                    "network": f"mesh-{radio}",
                    "type": "virtual",
                    "proto": "batadv_hardif",
                    "master": "bat0",
                    "mtu": 1536,
                }
            )

    return config


def make_wireless_config(device: Device, session: SessionDep):
    wireless_networks = session.exec(select(Wireless))
    radios = session.exec(
        select(Radio.radio_id).where(Radio.device_id == device.device_id)
    )

    config = []
    for radio in radios:
        for wireless in wireless_networks:
            wireless_config = {
                "name": f"{wireless.wireless_id}-{radio}",
                "type": "wireless",
                "wireless": {
                    "radio": radio,
                    "mode": "access_point",
                    "ssid": wireless.ssid,
                    "network": [wireless.network_id],
                },
            }
            if wireless.encryption:
                wireless_config["wireless"]["encryption"] = {
                    "protocol": wireless.encryption,
                    "key": wireless.key,
                }
            config.append(wireless_config)
        config.append(
            {
                "name": f"vwire-{radio}",
                "type": "wireless",
                "wireless": {
                    "radio": radio,
                    "mode": "802.11s",
                    "mesh_id": f"vwire-{radio}",
                    "network": ["mesh"],
                },
            }
        )
    return config


def make_radio_config(device: Device, session: SessionDep):
    radios = session.exec(
        select(Radio.radio_id).where(Radio.device_id == device.device_id)
    )

    config = []
    for radio in radios:
        config.append(
            {
                "name": radio,
                "type": "mac80211",
                "phy": radio.replace("radio", "phy"),
                "protocol": "802.11n",
                "band": "2g",
                "channel": 6,
                "channel_width": 20,
                "country": "GB",
            }
        )

    return config


def make_controller_config(device: Device, session: SessionDep):
    networks = session.exec(select(Network))
    return [
        {
            "config_name": "inform",
            "controller_ip": "192.168.122.1",
            "device_id": device.device_id,
            "management_network": [
                network.network_id for network in networks if network.management
            ][0],
        },
        {"config_name": "stun", "stun_interval": 20000, "stun_port": 3478},
    ]


def make_firewall_config(device: Device, session: SessionDep):
    networks = session.query(Network).all()
    internets = session.query(Internet).all()

    config = []
    wan_zone = {
        "config_name": "zone",
        "config_value": "wan",
        "name": "wan",
        "network": [
            internet.name.lower()
            for internet in internets
            if internet.device_id == device.device_id
        ],
        "input": "REJECT",
        "output": "ACCEPT",
        "forward": "REJECT",
        "masq": 1,
        "mtu_fix": 1,
    }
    config.append(wan_zone)

    for network in networks:
        if network.router_id == device.device_id:
            config.append(
                {
                    "config_name": "zone",
                    "config_value": network.network_id,
                    "name": network.network_id,
                    "network": [network.network_id],
                    "input": "ACCEPT",
                    "output": "ACCEPT",
                    "forward": "ACCEPT",
                }
            )
            config.append(
                {
                    "config_name": "forwarding",
                    "src": network.network_id,
                    "dest": "wan",
                }
            )

    config.extend(
        [
            {
                "config_name": "rule",
                "name": "Allow-DHCP-Renew",
                "src": "wan",
                "proto": "udp",
                "dest_port": 68,
                "target": "ACCEPT",
                "family": "ipv4",
            },
            {
                "config_name": "rule",
                "name": "Allow-Ping",
                "src": "wan",
                "proto": "icmp",
                "icmp_type": "echo-request",
                "target": "ACCEPT",
                "family": "ipv4",
            },
            {
                "config_name": "rule",
                "name": "Allow-IGMP",
                "src": "wan",
                "proto": "igmp",
                "target": "ACCEPT",
                "family": "ipv4",
            },
            {
                "config_name": "rule",
                "name": "Allow-DHCPv6",
                "src": "wan",
                "proto": "udp",
                "dest_port": 546,
                "target": "ACCEPT",
                "family": "ipv6",
            },
            {
                "config_name": "rule",
                "name": "Allow-MLD",
                "src": "wan",
                "proto": "icmp",
                "icmp_type": ["130/0", "131/0", "132/0", "143/0"],
                "target": "ACCEPT",
                "family": "ipv6",
            },
            {
                "config_name": "rule",
                "name": "Allow-ICMPv6-Input",
                "src": "wan",
                "proto": "icmp",
                "icmp_type": [
                    "echo-request",
                    "echo-reply",
                    "destination-unreachable",
                    "packet-too-big",
                    "time-exceeded",
                    "bad-header",
                    "unknown-header-type",
                    "router-solicitation",
                    "neighbour-solicitation",
                    "router-advertisement",
                    "neighbour-advertisement",
                ],
                "limit": "1000/sec",
                "target": "ACCEPT",
                "family": "ipv6",
            },
            {
                "config_name": "rule",
                "name": "Allow-ICMPv6-Forward",
                "src": "wan",
                "dest": "*",
                "proto": "icmp",
                "icmp_type": [
                    "echo-request",
                    "echo-reply",
                    "destination-unreachable",
                    "packet-too-big",
                    "time-exceeded",
                    "bad-header",
                    "unknown-header-type",
                ],
                "limit": "1000/sec",
                "target": "ACCEPT",
                "family": "ipv6",
            },
            {
                "config_name": "rule",
                "name": "Allow-IPSec-ESP",
                "src": "wan",
                "dest": [network.network_id for network in networks],
                "proto": "esp",
                "target": "ACCEPT",
            },
            {
                "config_name": "rule",
                "name": "Allow-ISAKMP",
                "src": "wan",
                "dest": [network.network_id for network in networks],
                "dest_port": 500,
                "proto": "udp",
                "target": "ACCEPT",
            },
        ]
    )
    return config


def make_dhcp_config(device: Device, session: SessionDep):
    networks = session.query(Network).all()
    config = [{"config_name": "dnsmasq"}]
    for network in networks:
        if network.dhcp_server_id == device.device_id:
            config.append(
                {
                    "config_name": "dhcp",
                    "interface": network.network_id,
                    "start": network.dhcp_offset,
                    "limit": network.dhcp_pool_size,
                    "dhcpv4": "server",
                    "leasetime": "12h",
                }
            )
    return config


@router.get("/netjsonconfig/{device_id}")
def get_router_netjson_config(device_id: uuid.UUID, session: SessionDep):
    device = session.get(Device, device_id)
    if not device:
        raise RuntimeError

    general = {
        "hostname": device.hostname.replace(" ", "-").replace("_", "-"),
        "description": device.hostname,
        "notes": "Configuration generated by OpenWrt Controller",
        "timezone": "Europe/London",
    }

    ntp = {
        "enabled": True,
        "enable_server": False,
        "server": [
            "0.openwrt.pool.ntp.org",
            "1.openwrt.pool.ntp.org",
            "2.openwrt.pool.ntp.org",
            "3.openwrt.pool.ntp.org",
        ],
    }

    config = {
        "type": "DeviceConfiguration",
        "general": general,
        "ntp": ntp,
        "interfaces": make_network_config(device, session),
        "controller": make_controller_config(device, session),
        "dhcp": make_dhcp_config(device, session),
    }

    if DeviceRole.AP in device.roles:
        config["interfaces"] += make_wireless_config(device, session)
        config["radios"] = make_radio_config(device, session)
    if DeviceRole.ROUTER in device.roles:
        config["firewall"] = make_firewall_config(device, session)
    return config


@router.get("/uci/{device_id}", response_class=PlainTextResponse)
def get_router_uci_config(device_id: uuid.UUID, session: SessionDep):
    config = get_router_netjson_config(device_id, session)
    ow = OpenWrt(config)
    return ow.render()


@router.get("/raw/{device_id}", response_class=Response)
def get_router_raw_config(device_id: uuid.UUID, session: SessionDep):
    config = get_router_netjson_config(device_id, session)
    ow = OpenWrt(config)
    archive = ow.generate()
    return Response(content=archive.getvalue(), media_type="application/gzip")


@router.get("/informd.tar.gz")
def get_device_file_archive():
    return FileResponse(pathlib.Path(__file__).parent / "informd.tar.gz")
