"""Tests for the thermal/battery safety automation — the safety-critical
core of Phase 6. hardware.sample_telemetry() and the mining/benchmark
runners are mocked so these run fast and deterministic; osascript is
mocked too (see test_notifications.py for that verification)."""

from unittest.mock import MagicMock, patch

import pytest

from macmine_lab import db, hardware, safety


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return db


def _telemetry(thermal_state="NORMAL", on_ac_power=True, battery_percent=100):
    return hardware.SystemTelemetry(
        battery=hardware.BatteryInfo(True, battery_percent, on_ac_power, on_ac_power, "charged" if on_ac_power else "discharging"),
        thermal=hardware.ThermalInfo(thermal_state, 100 if thermal_state == "NORMAL" else 60),
        cpu=hardware.CpuLoadInfo(10.0, 5.0, 85.0, 1.0, 1.0, 1.0),
        memory=hardware.MemoryInfo(25769803776, 20.0, 4.0),
    )


@pytest.fixture
def mocks(isolated_db):
    with patch.object(safety.hardware, "sample_telemetry") as mock_telemetry, \
         patch.object(safety.mining_runner, "is_running", return_value=False), \
         patch.object(safety.mining_runner, "stop") as mock_mining_stop, \
         patch.object(safety.mining_runner, "restart_with_threads") as mock_restart, \
         patch.object(safety.mining_runner, "snapshot") as mock_mining_snapshot, \
         patch.object(safety.benchmark_runner, "is_running", return_value=False), \
         patch.object(safety.miner, "stop_tracked") as mock_miner_stop, \
         patch.object(safety.notifications, "send") as mock_notify:
        mock_notify.return_value = True
        yield {
            "telemetry": mock_telemetry,
            "mining_running": safety.mining_runner.is_running,
            "mining_stop": mock_mining_stop,
            "restart": mock_restart,
            "mining_snapshot": mock_mining_snapshot,
            "benchmark_running": safety.benchmark_runner.is_running,
            "miner_stop": mock_miner_stop,
            "notify": mock_notify,
        }


def test_normal_thermal_nothing_active_takes_no_action(mocks):
    mocks["telemetry"].return_value = _telemetry("NORMAL")
    manager = safety.SafetyManager()
    manager.check_once()
    mocks["notify"].assert_not_called()
    mocks["mining_stop"].assert_not_called()


def test_critical_thermal_stops_mining_even_with_automation_disabled(mocks, isolated_db):
    db.set_setting("safety_automation_enabled", "false")  # hard floor: must still fire
    mocks["telemetry"].return_value = _telemetry("CRITICAL")
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["mining_stop"].assert_called_once_with(reason="thermal_critical_stop")
    mocks["notify"].assert_called_once()


def test_critical_thermal_stops_benchmark(mocks):
    mocks["telemetry"].return_value = _telemetry("CRITICAL")
    with patch.object(safety.benchmark_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["miner_stop"].assert_called_once()


def test_critical_thermal_with_nothing_active_does_nothing(mocks):
    mocks["telemetry"].return_value = _telemetry("CRITICAL")
    manager = safety.SafetyManager()
    manager.check_once()
    mocks["notify"].assert_not_called()
    mocks["mining_stop"].assert_not_called()


def test_warm_thermal_notifies_but_does_not_stop(mocks):
    mocks["telemetry"].return_value = _telemetry("WARM")
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["notify"].assert_called_once()
    mocks["mining_stop"].assert_not_called()


def test_warm_thermal_suppressed_when_automation_disabled(mocks, isolated_db):
    db.set_setting("safety_automation_enabled", "false")
    mocks["telemetry"].return_value = _telemetry("WARM")
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["notify"].assert_not_called()


def test_hot_thermal_reduces_mining_threads(mocks):
    mocks["telemetry"].return_value = _telemetry("HOT")
    with patch.object(safety.mining_runner, "is_running", return_value=True), \
         patch.object(safety.mining_runner, "snapshot") as snap:
        snap.return_value = MagicMock(threads=8)
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["restart"].assert_called_once_with(6, reason="thermal_hot_reduced")  # 8 - 25% = 6
    mocks["notify"].assert_called_once()


def test_hot_thermal_does_not_reduce_below_one_thread(mocks):
    mocks["telemetry"].return_value = _telemetry("HOT")
    with patch.object(safety.mining_runner, "is_running", return_value=True), \
         patch.object(safety.mining_runner, "snapshot") as snap:
        snap.return_value = MagicMock(threads=1)
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["restart"].assert_not_called()


def test_battery_ac_disconnected_stops_mining_by_default(mocks):
    mocks["telemetry"].return_value = _telemetry("NORMAL", on_ac_power=False, battery_percent=80)
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["mining_stop"].assert_called_once_with(reason="battery_ac_disconnected")


def test_battery_allowed_on_battery_but_below_threshold_stops(mocks, isolated_db):
    db.set_setting("allow_mining_on_battery", "true")
    db.set_setting("battery_pause_threshold_percent", "30")
    mocks["telemetry"].return_value = _telemetry("NORMAL", on_ac_power=False, battery_percent=20)
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["mining_stop"].assert_called_once_with(reason="battery_low")


def test_battery_allowed_on_battery_above_threshold_does_not_stop(mocks, isolated_db):
    db.set_setting("allow_mining_on_battery", "true")
    db.set_setting("battery_pause_threshold_percent", "30")
    mocks["telemetry"].return_value = _telemetry("NORMAL", on_ac_power=False, battery_percent=80)
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["mining_stop"].assert_not_called()


def test_battery_on_ac_power_never_triggers_battery_actions(mocks):
    mocks["telemetry"].return_value = _telemetry("NORMAL", on_ac_power=True, battery_percent=5)
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["mining_stop"].assert_not_called()


def test_battery_actions_gated_by_automation_toggle(mocks, isolated_db):
    db.set_setting("safety_automation_enabled", "false")
    mocks["telemetry"].return_value = _telemetry("NORMAL", on_ac_power=False, battery_percent=5)
    with patch.object(safety.mining_runner, "is_running", return_value=True):
        manager = safety.SafetyManager()
        manager.check_once()
    mocks["mining_stop"].assert_not_called()


def test_get_settings_defaults(isolated_db):
    settings = safety.get_settings()
    assert settings.automation_enabled is True
    assert settings.allow_mining_on_battery is False
    assert settings.battery_pause_threshold_percent == 30


def test_snapshot_reflects_real_telemetry_and_settings(mocks, isolated_db):
    mocks["telemetry"].return_value = _telemetry("WARM", on_ac_power=False, battery_percent=42)
    manager = safety.SafetyManager()
    state = manager.snapshot()
    assert state.thermal_state == "WARM"
    assert state.on_ac_power is False
    assert state.battery_percent == 42
    assert state.watching is False  # never started in this test
