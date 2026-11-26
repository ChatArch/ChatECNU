from __future__ import annotations

import socket
import struct
from unittest.mock import Mock

import pytest
import requests

from chatecnu import network_interface as network
from chatecnu.network_http import PythonNetworkAuthClient


INFO = {"interface": "en1", "source_ip": "192.0.2.2", "router_ip": "192.0.2.1", "dns_servers": ["192.0.2.53"]}


def test_adapter_binds_dns_tcp_and_source_without_modifying_global_resolver(monkeypatch):
    original = socket.getaddrinfo
    monkeypatch.setattr(network.socket, "if_nametoindex", lambda _: 13)
    resolver = Mock(return_value=["192.0.2.10"])
    connection = Mock(return_value=object())
    monkeypatch.setattr(network, "resolve_ipv4", resolver)
    monkeypatch.setattr(network, "create_connection", connection)
    with network.interface_session(INFO) as session:
        assert session.trust_env is False
        adapter = session.get_adapter("https://portal.example/")
        pool = adapter.poolmanager.connection_from_url("https://portal.example/")
        conn = pool._new_conn()
        conn._new_conn()
        assert conn.host == "portal.example"  # TLS and SNI must retain the hostname.
        resolver.assert_called_once_with("portal.example", "en1", "192.0.2.2", ["192.0.2.53"])
        assert connection.call_args.kwargs["source_address"] == ("192.0.2.2", 0)
        assert (socket.IPPROTO_IP, 25, 13) in connection.call_args.kwargs["socket_options"]
    assert socket.getaddrinfo is original


def test_adapters_do_not_change_other_sessions_pool_classes(monkeypatch):
    monkeypatch.setattr(network.socket, "if_nametoindex", lambda _: 13)
    regular = requests.Session()
    before = regular.get_adapter("https://").poolmanager.pool_classes_by_scheme.copy()
    with network.interface_session(INFO):
        assert regular.get_adapter("https://").poolmanager.pool_classes_by_scheme == before
    regular.close()


def test_interface_binding_rejects_binary_and_unsupported_platform(monkeypatch):
    with pytest.raises(ValueError, match="Python"):
        network.bind_client(Mock(), "en1")
    monkeypatch.setattr(network.platform, "system", lambda: "Linux")
    with pytest.raises(ValueError, match="macOS"):
        network.interface_info("en1")


def test_bind_client_keeps_endpoint_and_replaces_transport(monkeypatch):
    monkeypatch.setattr(network, "interface_info", lambda _: INFO)
    session = Mock()
    monkeypatch.setattr(network, "interface_session", lambda _: session)
    client = PythonNetworkAuthClient("https://portal.example", acid=7)
    assert network.bind_client(client, "en1") is client
    assert client.acid == 7 and client.base_url == "https://portal.example"
    assert client.session is session


@pytest.mark.parametrize("interface", ["-bad", "en1;echo", "en1\n", "x" * 100])
def test_invalid_interface_names_fail_before_subprocess(monkeypatch, interface):
    monkeypatch.setattr(network.platform, "system", lambda: "Darwin")
    run = Mock()
    monkeypatch.setattr(network, "command", run)
    with pytest.raises(ValueError, match="Invalid"):
        network.interface_info(interface)
    run.assert_not_called()


@pytest.mark.parametrize("address", ["192.0.2.11", "198.18.0.50"])
def test_dns_query_is_bound_and_rejects_fake_vpn_answers(monkeypatch, address):
    sock = Mock()
    sock.__enter__ = Mock(return_value=sock)
    sock.__exit__ = Mock(return_value=False)

    def answer(_):
        packet = sock.send.call_args.args[0]
        header = struct.pack("!6H", struct.unpack("!H", packet[:2])[0], 0x8180, 1, 1, 0, 0)
        return header + packet[12:] + b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 60, 4) + socket.inet_aton(address)

    sock.recv.side_effect = answer
    monkeypatch.setattr(network.socket, "socket", lambda *a: sock)
    monkeypatch.setattr(network.socket, "if_nametoindex", lambda _: 13)
    if address.startswith("198.18"):
        with pytest.raises(socket.gaierror):
            network.resolve_ipv4("portal.example", "en1", "192.0.2.2", ["192.0.2.53"])
    else:
        assert network.resolve_ipv4("portal.example", "en1", "192.0.2.2", ["192.0.2.53"]) == [address]
    sock.setsockopt.assert_called_with(socket.IPPROTO_IP, 25, 13)
    sock.bind.assert_called_with(("192.0.2.2", 0))
    sock.connect.assert_called_with(("192.0.2.53", 53))
