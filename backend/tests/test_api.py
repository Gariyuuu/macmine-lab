"""API tests. The background telemetry sampler and startup/shutdown hooks run
for real (against an isolated DB file) — only the actual XMRig benchmark
launch is mocked, since spawning a real 30s+ benchmark has no place in an
automated test suite that should run in well under a second.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from macmine_lab import api, db, paths


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(paths, "LOGS_DIR", tmp_path / "logs")
    (tmp_path / "logs").mkdir()
    # Slow the sampler way down so it doesn't race the test / hammer the CPU.
    monkeypatch.setattr(api, "TELEMETRY_SAMPLE_INTERVAL_S", 999)
    with TestClient(api.app) as c:
        yield c


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_hardware_returns_real_detected_fields(client):
    resp = client.get("/api/hardware")
    assert resp.status_code == 200
    body = resp.json()
    assert body["architecture"] == "arm64"
    assert "total_cores" in body


def test_telemetry_live(client):
    resp = client.get("/api/telemetry/live")
    assert resp.status_code == 200
    body = resp.json()
    assert "telemetry" in body
    assert "miner_running" in body
    assert body["miner_running"] is False


def test_integrity_404_when_nothing_recorded(client):
    resp = client.get("/api/integrity")
    assert resp.status_code == 404


def test_miner_status_when_nothing_running(client):
    resp = client.get("/api/miner/status")
    assert resp.status_code == 200
    assert resp.json()["running"] is False


def test_miner_stop_when_nothing_running_is_a_noop_success(client):
    resp = client.post("/api/miner/stop")
    assert resp.status_code == 200
    assert resp.json() == {"stopped": True}


def test_benchmark_start_rejects_bad_duration(client):
    resp = client.post("/api/benchmark/start", params={"duration_seconds": 45})
    assert resp.status_code == 400


def test_benchmark_start_rejects_when_xmrig_not_installed(client):
    with patch.object(api.integrity, "find_xmrig_binary", return_value=None):
        resp = client.post("/api/benchmark/start", params={"duration_seconds": 30})
    assert resp.status_code == 409


def test_benchmark_start_invokes_runner_without_launching_real_xmrig(client):
    with patch.object(api.benchmark_runner, "start") as mock_start:
        resp = client.post(
            "/api/benchmark/start", params={"threads": 4, "duration_seconds": 30}
        )
    assert resp.status_code == 200
    assert resp.json() == {"started": True, "threads": 4, "duration_seconds": 30}
    mock_start.assert_called_once_with(4, 30)


def test_benchmark_live_when_idle(client):
    resp = client.get("/api/benchmark/live")
    assert resp.status_code == 200
    assert resp.json()["running"] is False


def test_benchmark_history_empty(client):
    resp = client.get("/api/benchmark/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_benchmark_run_404_when_missing(client):
    resp = client.get("/api/benchmark/9999")
    assert resp.status_code == 404


def test_latest_log_empty_when_nothing_has_run(client):
    resp = client.get("/api/logs/latest")
    assert resp.status_code == 200
    assert resp.json() == {"log_file": None, "lines": []}


def test_latest_log_tails_most_recent_file(client):
    (paths.LOGS_DIR / "old.log").write_text("old line 1\nold line 2\n")
    import time as _time
    _time.sleep(0.01)
    (paths.LOGS_DIR / "new.log").write_text("\n".join(f"line {i}" for i in range(300)) + "\n")

    resp = client.get("/api/logs/latest?lines=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["log_file"] == "new.log"
    assert body["lines"] == [f"line {i}" for i in range(295, 300)]


def test_websocket_streams_real_payload(client):
    with client.websocket_connect("/ws/live") as ws:
        payload = ws.receive_json()
    assert "telemetry" in payload
    assert "miner" in payload
    assert "benchmark" in payload
    assert "mining" in payload
    assert payload["miner"]["running"] is False
    assert payload["mining"]["running"] is False


# --- Wallets -----------------------------------------------------------

_VALID_ADDRESS = "4" + "x" * 94


def test_validate_wallet_endpoint_valid(client):
    resp = client.post("/api/wallets/validate", json={"address": _VALID_ADDRESS})
    assert resp.status_code == 200
    assert resp.json()["valid"] is True
    assert resp.json()["kind"] == "standard"


def test_validate_wallet_endpoint_invalid(client):
    resp = client.post("/api/wallets/validate", json={"address": "not-a-real-address"})
    assert resp.status_code == 200
    assert resp.json()["valid"] is False


def test_create_wallet_rejects_bad_format(client):
    resp = client.post("/api/wallets", json={"address": "bad"})
    assert resp.status_code == 400


def test_create_and_list_and_delete_wallet(client):
    resp = client.post("/api/wallets", json={"address": _VALID_ADDRESS, "label": "Test"})
    assert resp.status_code == 200
    wallet_id = resp.json()["id"]
    assert resp.json()["address_kind"] == "standard"

    listed = client.get("/api/wallets").json()
    assert len(listed) == 1

    del_resp = client.delete(f"/api/wallets/{wallet_id}")
    assert del_resp.status_code == 200
    assert client.get("/api/wallets").json() == []


def test_delete_wallet_404_when_missing(client):
    resp = client.delete("/api/wallets/9999")
    assert resp.status_code == 404


# --- Pools -----------------------------------------------------------

def test_create_list_delete_pool(client):
    resp = client.post(
        "/api/pools",
        json={"name": "Test Pool", "host": "pool.example.com", "port": 3333, "tls": False},
    )
    assert resp.status_code == 200
    pool_id = resp.json()["id"]

    listed = client.get("/api/pools").json()
    assert len(listed) == 1

    del_resp = client.delete(f"/api/pools/{pool_id}")
    assert del_resp.status_code == 200
    assert client.get("/api/pools").json() == []


def test_pool_connection_test_endpoint_reports_real_failure(client):
    # Nothing is listening on this port — a genuine, unmocked failure.
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    resp = client.post(
        "/api/pools/test-connection", json={"host": "127.0.0.1", "port": port, "tls": False}
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is False


# --- Mining ------------------------------------------------------------

def test_mining_start_404_missing_pool(client):
    resp = client.post(
        "/api/mining/start", json={"pool_id": 9999, "wallet_id": 9999, "threads": 4}
    )
    assert resp.status_code == 404


def test_mining_start_404_missing_wallet(client):
    pool_resp = client.post(
        "/api/pools", json={"name": "P", "host": "pool.example.com", "port": 3333, "tls": False}
    )
    pool_id = pool_resp.json()["id"]
    resp = client.post(
        "/api/mining/start", json={"pool_id": pool_id, "wallet_id": 9999, "threads": 4}
    )
    assert resp.status_code == 404


def test_mining_start_invokes_runner_without_launching_real_xmrig(client):
    pool_resp = client.post(
        "/api/pools", json={"name": "P", "host": "pool.example.com", "port": 3333, "tls": False}
    )
    pool_id = pool_resp.json()["id"]
    wallet_resp = client.post("/api/wallets", json={"address": _VALID_ADDRESS})
    wallet_id = wallet_resp.json()["id"]

    with patch.object(api.mining_runner, "start") as mock_start:
        resp = client.post(
            "/api/mining/start", json={"pool_id": pool_id, "wallet_id": wallet_id, "threads": 4}
        )
    assert resp.status_code == 200
    assert resp.json()["started"] is True
    mock_start.assert_called_once()


def test_mining_live_when_idle(client):
    resp = client.get("/api/mining/live")
    assert resp.status_code == 200
    assert resp.json()["running"] is False


def test_mining_stop_when_idle_is_safe(client):
    resp = client.post("/api/mining/stop")
    assert resp.status_code == 200
    assert resp.json() == {"stopping": True}


def test_mining_history_empty(client):
    resp = client.get("/api/mining/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_mining_session_404_when_missing(client):
    resp = client.get("/api/mining/9999")
    assert resp.status_code == 404
