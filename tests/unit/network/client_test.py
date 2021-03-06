# -*- coding: utf-8 -*-
"""network.client module tests"""

import random
import socket
import threading

import pytest
from localchat.network import client, config, server, util

port = None


class ServerSocket:
    """Server socket. Runs the server on localhost"""

    def __init__(self):
        self.server_thread = None

    def __enter__(self):
        server.init(port=port)
        self.server_thread = threading.Thread(target=server.run_forever, daemon=True)
        self.server_thread.start()
        return self

    def __exit__(self, *_):
        server.socket_.close()
        server.kill()


def setup():
    global port  # pylint: disable=global-statement
    port = random.randint(10000, 65535)
    print("setup", port)


def teardown():
    if server.socket_:
        server.socket_.close()


@pytest.mark.parametrize("ip_address", [util.get_host_ip()])
def test_network_connection_fail(ip_address):
    with pytest.raises(client.StartConnectionError):
        client.NetworkConnection(ip_address, port=port, timeout=0.2).connect()


@pytest.mark.parametrize("ip_address", ["127.0.0.2"])
def test_wrong_server_ip(ip_address):
    with ServerSocket():
        with pytest.raises(client.StartConnectionError):
            client.NetworkConnection(ip_address, port=port, timeout=0.2).connect()


@pytest.mark.parametrize("ip_address", [util.get_host_ip()])
def test_connect(ip_address):
    with ServerSocket():
        conn = client.NetworkConnection(ip_address, port=port)
        conn.connect()
        assert conn.id is not None
        assert bool(conn)


@pytest.mark.parametrize("ip_address", [util.get_host_ip()])
def test_send_fail(ip_address):
    conn = client.NetworkConnection(ip_address, port=port, timeout=0.5)
    with ServerSocket():
        conn.connect()
        response = conn.send("abc".encode())
    assert response is None


@pytest.mark.parametrize(
    "head, body, expected_response_status",
    [("abc", "", 400), ("get/clients", "", 200)],
)
def test_send_request(head, body, expected_response_status):
    conn = client.NetworkConnection(ip_address=util.get_host_ip(), port=port)
    with ServerSocket():
        conn.connect()
        response = conn.send_request(head=head, body=body)
    assert response.get("status") == expected_response_status


@pytest.mark.parametrize("ip_address", [util.get_host_ip()])
def test_bool(ip_address):
    conn = client.NetworkConnection(ip_address, port=port)
    assert not bool(conn)


@pytest.mark.parametrize("ip_address", [util.get_host_ip()])
def test_close(ip_address):
    conn = client.NetworkConnection(ip_address, port=port, timeout=0.5)
    with ServerSocket():
        conn.connect()
        conn.close()
    assert conn.id is None
    with pytest.raises(socket.error):
        conn.socket.recv(config.CHUNKSIZE)
