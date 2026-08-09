"""Pool connection testing.

This is a plain TCP (and, for TLS pools, TLS handshake) reachability check
against the configured host:port. It deliberately does NOT speak the
Stratum mining protocol or send a wallet address — it only proves the pool
server is reachable over the network. Whether a wallet+pool combination
actually works (the pool accepts the address, issues jobs, and credits
shares) is only provable by actually mining, which is what starting a real
mining session shows live via accepted/rejected share counts.
"""

from __future__ import annotations

import socket
import ssl
import time
from dataclasses import dataclass


@dataclass
class ConnectionTestResult:
    success: bool
    latency_ms: float | None
    message: str


def test_pool_connection(host: str, port: int, tls: bool, timeout: float = 5.0) -> ConnectionTestResult:
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            if tls:
                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=host):
                    pass  # handshake completing without raising is the test
            latency_ms = round((time.monotonic() - start) * 1000, 1)
            suffix = " over TLS" if tls else ""
            return ConnectionTestResult(True, latency_ms, f"Connected to {host}:{port}{suffix}.")
    except socket.timeout:
        return ConnectionTestResult(False, None, f"Timed out connecting to {host}:{port} after {timeout}s.")
    except socket.gaierror as e:
        return ConnectionTestResult(False, None, f"DNS lookup failed for '{host}': {e}")
    except ssl.SSLError as e:
        return ConnectionTestResult(False, None, f"TLS handshake failed: {e}")
    except OSError as e:
        return ConnectionTestResult(False, None, f"Connection failed: {e}")
