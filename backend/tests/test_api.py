"""API tests. The background telemetry sampler and startup/shutdown hooks run
for real (against an isolated DB file) — only the actual XMRig benchmark
launch is mocked, since spawning a real 30s+ benchmark has no place in an
automated test suite that should run in well under a second.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from macmine_lab import api, db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
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


def test_websocket_streams_real_payload(client):
    with client.websocket_connect("/ws/live") as ws:
        payload = ws.receive_json()
    assert "telemetry" in payload
    assert "miner" in payload
    assert "benchmark" in payload
    assert payload["miner"]["running"] is False
