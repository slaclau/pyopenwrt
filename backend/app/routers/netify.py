import os
import pprint
import time
from ipaddress import IPv4Address

import gzip
import json
from operator import getitem

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import SQLModel, Field, Relationship, and_, desc, asc
from pydantic_extra_types.mac_address import MacAddress

router = APIRouter(prefix="/netify", tags=["netify"])

from ..dependencies import SessionDep


class FlowBase(SQLModel):
    digest: str = Field(primary_key=True)
    application: str = Field()
    protocol: str = Field()

    vlan_id: int | None = Field()
    active: bool = Field()
    first_seen_at: int | None = Field()

    local_ip: IPv4Address | None = Field()
    local_port: int | None = Field()
    local_mac: MacAddress | None = Field()

    other_ip: IPv4Address | None = Field()
    other_port: int | None = Field()
    other_mac: MacAddress | None = Field()


class FlowStats(SQLModel, table=True):
    digest: str = Field(primary_key=True, foreign_key="flow.digest")
    last_seen_at: int = Field(primary_key=True)

    local_bytes: int = Field()
    other_bytes: int = Field()
    local_rate: float = Field()
    other_rate: float = Field()

    flow: "Flow" = Relationship(back_populates="stats")


class Flow(FlowBase, table=True):
    stats: list[FlowStats] = Relationship(back_populates="flow")


class FlowWithStats(FlowBase):
    stats: list[FlowStats]


class HostStats(SQLModel, table=True):
    timestamp: int = Field(primary_key=True)
    application: str = Field(primary_key=True)
    protocol: str = Field(primary_key=True)
    mac: MacAddress = Field(primary_key=True)
    ip: IPv4Address = Field(primary_key=True)
    upload: float = Field()
    download: float = Field()


@router.post("/")
async def netify(request: Request, session: SessionDep):
    payload = json.loads(gzip.decompress(await request.body()))
    if "type" not in payload:
        print(payload.keys())
        return

    match payload["type"]:
        case "flow":
            create_netify_flow(payload["flow"], session)
        case "flow_dpi_update":
            update_netify_flow(payload["flow"], session)
        case "flow_dpi_complete":
            complete_netify_flow(payload["flow"], session)
        case "flow_purge":
            complete_netify_flow(payload["flow"], session, True)
        case "flow_stats":
            add_flow_stats(payload, session)
        case ("agent_status" | "interface_stats" | "interfaces" | "global_stats"):
            pass
        case _:
            print(payload["type"])
            pprint.pprint(payload)
            # print(payload.keys())
            if "reason" in payload:
                pass
                # print(payload["reason"])
            if "flow" in payload:
                pass
                # print(payload["flow"].keys())


def create_netify_flow(flow, session: SessionDep):
    session.merge(
        Flow(
            application=flow.get("detected_application_name", ""),
            protocol=flow.get("detected_protocol_name", ""),
            active=True,
            **flow,
        )
    )
    session.commit()


def update_netify_flow(flow, session: SessionDep):
    flow_stats = FlowStats(**flow)
    session.merge(flow_stats)
    original = session.get(Flow, flow["digest"])
    new = Flow(
        application=flow["detected_application_name"],
        protocol=flow["detected_protocol_name"],
        active=True,
        **flow,
    )
    if original:
        assert original.first_seen_at == new.first_seen_at
    session.merge(new)
    session.commit()


def complete_netify_flow(flow, session: SessionDep, purge=False):
    flow_stats = FlowStats(**flow)
    session.merge(flow_stats)
    old = session.get(Flow, flow["digest"])
    if old:
        old.active = False
        session.commit()


def add_flow_stats(payload, session: SessionDep):
    flow_stats = FlowStats(**payload["flow"])
    session.merge(flow_stats)
    flow = session.get(Flow, payload["flow"]["digest"])
    if not flow:
        create_netify_flow(payload["flow"], session)
        flow = session.get(Flow, payload["flow"]["digest"])

    if not flow.local_ip or not flow.local_mac:
        return

    host_stats = (
        session.query(HostStats)
        .where(
            and_(
                HostStats.application == flow.application,
                HostStats.protocol == flow.protocol,
                HostStats.mac == flow.local_mac,
                HostStats.ip == flow.local_ip,
            )
        )
        .order_by(desc("timestamp"))
        .first()
    )
    if host_stats is None:
        upload = 0
        download = 0
    else:
        upload = host_stats.upload
        download = host_stats.download
    host_stats = HostStats(
        timestamp=flow_stats.last_seen_at,
        application=flow.application,
        protocol=flow.protocol,
        mac=flow.local_mac,
        ip=flow.local_ip,
        upload=upload + flow_stats.local_bytes,
        download=download + flow_stats.other_bytes,
    )
    session.merge(host_stats)
    session.commit()


@router.get("/flows")
def get_flows(session: SessionDep) -> list[Flow]:
    return session.query(Flow).all()


@router.get("/flows/{digest}")
def get_flow_stats(digest: str, session: SessionDep) -> FlowWithStats:
    return session.get(Flow, digest)


@router.get("/flows/active")
def get_active_flows(session: SessionDep) -> list[Flow]:
    return session.query(Flow).where(Flow.active).all()


class TimeStats(BaseModel):
    flows: list[Flow] = Field()
    stats: list[FlowStats] = Field()


@router.get("/stats/last_hour")
def get_last_hour_stats(session: SessionDep) -> TimeStats:
    stats = (
        session.query(FlowStats)
        .where(FlowStats.last_seen_at / 1000 >= time.time() - 3600)
        .all()
    )
    digests = {stat.digest for stat in stats}
    flows = session.query(Flow).where(Flow.digest.in_(digests)).all()
    return TimeStats(flows=flows, stats=stats)


@router.get("/stats/by_host/last_day")
def get_host_last_hour_stats(session: SessionDep):
    return get_host_time_stats(session, time.time() - 3600 * 24, time.time())


@router.get("/stats/by_host/last_week")
def get_host_last_hour_stats(session: SessionDep):
    return get_host_time_stats(session, time.time() - 3600 * 24 * 7, time.time())


@router.get("/stats/by_host/last_month")
def get_host_last_hour_stats(session: SessionDep):
    return get_host_time_stats(session, time.time() - 60 * 24 * 30, time.time())


def get_host_time_stats(session: SessionDep, start_time, end_time, transform=True):
    t = time.time()
    identifiers = (
        session.query(
            HostStats.application, HostStats.protocol, HostStats.mac, HostStats.ip
        )
        .where(HostStats.timestamp >= start_time * 1000)
        .distinct()
    )
    rtn = {"raw": [], "hosts": [], "categories": []}

    stats = (
        session.query(
            HostStats.application,
            HostStats.protocol,
            HostStats.mac,
            HostStats.ip,
            func.min(HostStats.download).label("start_download"),
            func.min(HostStats.upload).label("start_upload"),
            func.max(HostStats.download).label("end_download"),
            func.max(HostStats.upload).label("end_upload"),
        )
        .where(
            and_(
                HostStats.timestamp >= start_time * 1000,
                HostStats.timestamp <= end_time * 1000,
            )
        )
        .group_by(
            HostStats.application, HostStats.protocol, HostStats.mac, HostStats.ip
        )
    )

    for stat in stats:
        res = {
            "application": stat.application,
            "protocol": (
                stat.protocol
                if not transform
                else stat.protocol if stat.application == "Unknown" else ""
            ),
            "mac": stat.mac,
            "ip": stat.ip,
            "download": stat.end_download - stat.start_download,
            "upload": stat.end_upload - stat.start_upload,
        }
        rtn["raw"].append(res)
    hosts = {(identifier.mac, identifier.ip) for identifier in identifiers}
    for host in hosts:
        host_data = [
            raw_stat
            for raw_stat in rtn["raw"]
            if raw_stat["mac"] == host[0] and raw_stat["ip"] == host[1]
        ]
        download = sum([raw_stat["download"] for raw_stat in host_data])
        upload = sum([raw_stat["upload"] for raw_stat in host_data])
        rtn["hosts"].append(
            {"mac": host[0], "ip": host[1], "download": download, "upload": upload}
        )
    categories = {
        (
            identifier.application,
            (
                identifier.protocol
                if not transform
                else identifier.protocol if identifier.application == "Unknown" else ""
            ),
        )
        for identifier in identifiers
    }
    for category in categories:
        category_data = [
            raw_stat
            for raw_stat in rtn["raw"]
            if raw_stat["application"] == category[0]
            and raw_stat["protocol"] == category[1]
        ]
        download = sum([raw_stat["download"] for raw_stat in category_data])
        upload = sum([raw_stat["upload"] for raw_stat in category_data])
        rtn["categories"].append(
            {
                "application": category[0],
                "protocol": category[1],
                "download": download,
                "upload": upload,
            }
        )
    rtn["raw"].sort(key=lambda x: x["upload"] + x["download"], reverse=True)
    rtn["hosts"].sort(key=lambda x: x["upload"] + x["download"], reverse=True)
    rtn["categories"].sort(key=lambda x: x["upload"] + x["download"], reverse=True)
    return rtn


def get_host_time_stats_from_raw(session: SessionDep, start_time, end_time):
    t = time.time()
    raw = session.query(FlowStats).where(
        and_(
            FlowStats.last_seen_at / 1000 >= start_time,
            FlowStats.last_seen_at / 1000 <= end_time,
        )
    )
    print(f"sql took {time.time() - t:.3} s")
    flows = [stat.flow for stat in raw]
    hosts = set([(flow.local_mac, flow.local_ip) for flow in flows if flow])
    rtn = {"hosts": [], "categories": []}
    for host in hosts:
        host_stats = [
            stat
            for stat in raw
            if stat.flow
            and stat.flow.local_mac == host[0]
            and stat.flow.local_ip == host[1]
        ]
        categories = set(
            [(stat.flow.application, stat.flow.protocol) for stat in host_stats]
        )
        host_rtn = []
        for category in categories:
            category_stats = [
                stat
                for stat in host_stats
                if stat.flow
                and stat.flow.application == category[0]
                and stat.flow.protocol == category[1]
            ]
            local_bytes = sum([stat.local_bytes for stat in category_stats])
            other_bytes = sum([stat.other_bytes for stat in category_stats])
            host_rtn.append(
                {
                    "application": category[0],
                    "protocol": category[1],
                    "upload": local_bytes,
                    "download": other_bytes,
                }
            )
        host_rtn.sort(
            key=lambda category: category["upload"] + category["download"], reverse=True
        )
        total_upload = sum([stat["upload"] for stat in host_rtn])
        total_download = sum([stat["download"] for stat in host_rtn])
        rtn["hosts"].append(
            {
                "mac": host[0],
                "ip": host[1],
                "stats": host_rtn,
                "upload": total_upload,
                "download": total_download,
            }
        )
    print(f"aggregate stats by host took {time.time() - t:.3} s")
    total_upload = sum([host["upload"] for host in rtn["hosts"]])
    total_download = sum([host["download"] for host in rtn["hosts"]])
    rtn["upload"] = total_upload
    rtn["download"] = total_download

    rtn["hosts"].sort(key=lambda host: host["upload"] + host["download"], reverse=True)

    categories = set(
        [
            (category["application"], category["protocol"])
            for host in rtn["hosts"]
            for category in host["stats"]
        ]
    )
    for category in categories:
        stats = [
            stat
            for host in rtn["hosts"]
            for stat in host["stats"]
            if stat["application"] == category[0] and stat["protocol"] == category[1]
        ]
        total_upload = sum([stat["upload"] for stat in stats])
        total_download = sum([stat["download"] for stat in stats])
        category_rtn = {
            "application": category[0],
            "protocol": category[1],
            "upload": total_upload,
            "download": total_download,
        }
        rtn["categories"].append(category_rtn)
    rtn["categories"].sort(
        key=lambda category: category["upload"] + category["download"], reverse=True
    )
    print(f"retrieving stats took {time.time() - t:.3} s")
    return rtn


@router.get("/applications")
def get_applications_map() -> dict[str, str]:
    return {
        "netify.youtube": "YouTube",
        "netify.bbc": "BBC",
        "netify.ntp": "NTP",
        "netify.reverse-dns": "Reverse DNS",
    }
