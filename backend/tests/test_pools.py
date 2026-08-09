"""Tests for the pool connection test — real TCP/TLS reachability checks
against a local test server, not a mocked network layer. No wallet or
mining protocol is involved here, only the raw socket connect."""

import socket
import threading

import pytest

from macmine_lab import pools


@pytest.fixture
def local_tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    stop = threading.Event()

    def accept_loop():
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
                conn.close()
            except socket.timeout:
                continue
            except OSError:
                break

    thread = threading.Thread(target=accept_loop, daemon=True)
    thread.start()
    yield port
    stop.set()
    server.close()
    thread.join(timeout=1)


def test_connects_to_real_local_server(local_tcp_server):
    result = pools.test_pool_connection("127.0.0.1", local_tcp_server, tls=False, timeout=2.0)
    assert result.success is True
    assert result.latency_ms is not None
    assert "Connected" in result.message


def test_connection_refused_when_nothing_listening():
    # Bind-and-close to get a genuinely free port with nothing listening.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    result = pools.test_pool_connection("127.0.0.1", port, tls=False, timeout=2.0)
    assert result.success is False
    assert result.latency_ms is None


def test_dns_failure_reported_clearly():
    result = pools.test_pool_connection("this-host-should-not-resolve.invalid", 3333, tls=False, timeout=2.0)
    assert result.success is False
    assert "DNS" in result.message or "resolve" in result.message.lower()


def test_tls_handshake_fails_against_plain_tcp_server(local_tcp_server):
    # Requesting TLS against a server that never speaks TLS should fail
    # cleanly, not hang or crash.
    result = pools.test_pool_connection("127.0.0.1", local_tcp_server, tls=True, timeout=2.0)
    assert result.success is False
