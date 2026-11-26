"""macOS interface-bound DNS and HTTP without changing system routes."""
from __future__ import annotations

import ipaddress
import platform
import re
import secrets
import socket
import struct
import subprocess

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import NewConnectionError
from urllib3.util.connection import create_connection

IP_BOUND_IF = 25


def command(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        raise ValueError("Interface inspection timed out.") from None
    return result.stdout.strip() if result.returncode == 0 else ""


def interface_info(interface: str) -> dict:
    if platform.system() != "Darwin":
        raise ValueError("--interface currently supports macOS only.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,31}", interface):
        raise ValueError("Invalid network interface name.")
    source = command(["/usr/sbin/ipconfig", "getifaddr", interface])
    try:
        ipaddress.IPv4Address(source)
    except ValueError:
        raise ValueError("Selected interface has no IPv4 connection.") from None
    routers = command(["/usr/sbin/ipconfig", "getoption", interface, "router"]).split()
    if not routers:
        raise ValueError("Selected interface has no DHCP router.")
    router = str(ipaddress.IPv4Address(routers[0]))
    dns = command(["/usr/sbin/ipconfig", "getoption", interface, "domain_name_server"]).split()
    servers = [str(ipaddress.IPv4Address(value)) for value in dns]
    if not servers:
        raise ValueError("Selected interface has no DHCP DNS servers.")
    return {"interface": interface, "source_ip": source, "router_ip": router, "dns_servers": servers}


def router_mac(interface: str, router: str) -> str:
    neighbor = command(["/usr/sbin/arp", "-n", router]).lower()
    if "incomplete" in neighbor or not neighbor:
        command(["/sbin/ping", "-n", "-c", "1", "-W", "300", "-b", interface, router])
        neighbor = command(["/usr/sbin/arp", "-n", router]).lower()
    match = re.search(r" at ([0-9a-f:]+) on (\S+)", neighbor)
    if not match or match[2] != interface or len(match[1].split(":")) != 6:
        raise ValueError("Selected interface's router could not be identified.")
    return ":".join(part.zfill(2) for part in match[1].split(":"))


def resolve_ipv4(host: str, interface: str, source: str, servers: list[str]) -> list[str]:
    try:
        return [str(ipaddress.IPv4Address(host))]
    except ValueError:
        pass
    labels = host.encode("idna").split(b".")
    if any(not label or len(label) > 63 for label in labels) or len(host) > 253:
        raise socket.gaierror("Invalid DNS name")
    question = b"".join(bytes([len(label)]) + label for label in labels) + b"\0"
    for server in servers[:2]:
        transaction = secrets.randbelow(65536)
        packet = struct.pack("!6H", transaction, 0x100, 1, 0, 0, 0) + question + struct.pack("!HH", 1, 1)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(2)
                sock.setsockopt(socket.IPPROTO_IP, IP_BOUND_IF, socket.if_nametoindex(interface))
                sock.bind((source, 0))
                sock.connect((server, 53))
                sock.send(packet)
                data = sock.recv(8192)
            ident, flags, questions, answers, _, _ = struct.unpack("!6H", data[:12])
            if ident != transaction or flags & 15 or flags & 0x200 or not flags & 0x8000:
                continue

            def skip(offset: int) -> int:
                for _ in range(128):
                    size = data[offset]
                    if size == 0:
                        return offset + 1
                    if size & 0xc0 == 0xc0:
                        return offset + 2
                    offset += 1 + size
                raise ValueError("Invalid DNS name")

            offset = 12
            for _ in range(questions):
                offset = skip(offset) + 4
            addresses = []
            for _ in range(answers):
                offset = skip(offset)
                kind, family, _, size = struct.unpack("!HHIH", data[offset:offset + 10])
                offset += 10
                if kind == 1 and family == 1 and size == 4:
                    address = socket.inet_ntoa(data[offset:offset + size])
                    if ipaddress.IPv4Address(address) not in ipaddress.IPv4Network("198.18.0.0/15"):
                        addresses.append(address)
                offset += size
            if addresses:
                return list(dict.fromkeys(addresses))[:2]
        except (OSError, ValueError, IndexError, struct.error):
            continue
    raise socket.gaierror("Interface DNS lookup failed")


class BoundAdapter(HTTPAdapter):
    """Resolve on this adapter only; keep the original hostname for TLS/SNI."""

    def __init__(self, info: dict):
        self.info = info
        super().__init__(max_retries=0)

    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        info = self.info

        class BoundConnection:
            def _new_conn(self):
                try:
                    addresses = resolve_ipv4(self.host, info["interface"], info["source_ip"], info["dns_servers"])
                    for address in addresses:
                        try:
                            return create_connection((address, self.port), self.timeout,
                                                     source_address=self.source_address,
                                                     socket_options=self.socket_options)
                        except OSError:
                            continue
                except OSError:
                    pass
                raise NewConnectionError(self, "Interface connection failed")

        class BoundHTTP(BoundConnection, HTTPConnection):
            pass

        class BoundHTTPS(BoundConnection, HTTPSConnection):
            pass

        class HTTPPool(HTTPConnectionPool):
            ConnectionCls = BoundHTTP

        class HTTPSPool(HTTPSConnectionPool):
            ConnectionCls = BoundHTTPS

        kwargs["source_address"] = (info["source_ip"], 0)
        kwargs["socket_options"] = [
            (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
            (socket.IPPROTO_IP, IP_BOUND_IF, socket.if_nametoindex(info["interface"])),
        ]
        super().init_poolmanager(connections, maxsize, block=block, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {"http": HTTPPool, "https": HTTPSPool}


def interface_session(info: dict) -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.mount("https://", BoundAdapter(info))
    session.mount("http://", BoundAdapter(info))
    return session


def bind_client(client, interface: str | None):
    if interface is None:
        return client
    from chatecnu.network_http import PythonNetworkAuthClient

    if not isinstance(client, PythonNetworkAuthClient):
        raise ValueError("--interface requires the Python network backend.")
    session = interface_session(interface_info(interface))
    client.session.close()
    client.session = session
    return client
