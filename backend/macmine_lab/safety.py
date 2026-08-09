"""Automated thermal + battery safety actions.

Runs as a background thread (same pattern as the telemetry sampler),
checking real telemetry every CHECK_INTERVAL_S and taking real, auditable
action whenever mining or a benchmark is active:

  NORMAL   -> no action
  WARM     -> notify once (rate-limited), no automatic changes
  HOT      -> notify + reduce mining threads by ~25% (benchmark mode: notify
              only — a benchmark's fixed short duration and single-shot API
              contract make live reconfiguration more complex/risky than
              it's worth; this is a deliberate scope limit, documented here)
  CRITICAL -> notify + stop whatever is running, unconditionally

CRITICAL-stop is a hard safety floor: it is NOT gated by the automation
toggle below, matching the project's stance against ever bypassing
thermal protection. WARM/HOT behavior and battery protection can be
toggled off if you want fully manual control.

Battery: while mining (not benchmarking — benchmarks are short and
user-initiated), disconnecting AC power stops mining unless "allow mining
on battery" is explicitly enabled. Even when that's enabled, mining still
stops if battery drops below a configurable percentage. All of it reads
real telemetry from hardware.py — nothing here invents a temperature or a
battery percentage.
"""

from __future__ import annotations

import datetime
import threading
from dataclasses import dataclass

from . import db, hardware, miner, notifications
from .mining_runner import mining_runner
from .runner import benchmark_runner

CHECK_INTERVAL_S = 8
THERMAL_THREAD_REDUCTION_FRACTION = 0.25

DEFAULT_AUTOMATION_ENABLED = "true"
DEFAULT_ALLOW_MINING_ON_BATTERY = "false"
DEFAULT_BATTERY_PAUSE_THRESHOLD_PERCENT = "30"


@dataclass
class SafetySettings:
    automation_enabled: bool
    allow_mining_on_battery: bool
    battery_pause_threshold_percent: int


@dataclass
class SafetyState:
    watching: bool
    thermal_state: str
    on_ac_power: bool | None
    battery_percent: int | None
    automation_enabled: bool
    allow_mining_on_battery: bool
    battery_pause_threshold_percent: int
    last_action: str | None
    last_action_at: str | None


def get_settings() -> SafetySettings:
    return SafetySettings(
        automation_enabled=db.get_setting("safety_automation_enabled", DEFAULT_AUTOMATION_ENABLED) == "true",
        allow_mining_on_battery=db.get_setting(
            "allow_mining_on_battery", DEFAULT_ALLOW_MINING_ON_BATTERY
        ) == "true",
        battery_pause_threshold_percent=int(
            db.get_setting("battery_pause_threshold_percent", DEFAULT_BATTERY_PAUSE_THRESHOLD_PERCENT)
        ),
    )


class SafetyManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_action: str | None = None
        self._last_action_at: str | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _record_action(self, action: str) -> None:
        with self._lock:
            self._last_action = action
            self._last_action_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.check_once()
            except Exception:
                pass  # one failed check must never kill the watcher thread
            self._stop_event.wait(CHECK_INTERVAL_S)

    def check_once(self) -> None:
        settings = get_settings()
        telemetry = hardware.sample_telemetry()
        mining_active = mining_runner.is_running()
        benchmark_active = benchmark_runner.is_running()
        any_active = mining_active or benchmark_active
        thermal = telemetry.thermal.state

        # Hard floor — always enforced, never gated by the automation toggle.
        if thermal == "CRITICAL" and any_active:
            notifications.send(
                "MacMine Lab", "Mac reached critical thermal state — mining stopped.", "thermal_critical"
            )
            if mining_active:
                mining_runner.stop(reason="thermal_critical_stop")
            if benchmark_active:
                miner.stop_tracked()
            self._record_action("thermal_critical_stop")
            return

        if not settings.automation_enabled:
            return

        if thermal == "WARM" and any_active:
            notifications.send(
                "MacMine Lab", "Your Mac is warming up — keep an eye on it.", "thermal_warm"
            )
            self._record_action("thermal_warm_notify")

        elif thermal == "HOT" and any_active:
            notifications.send(
                "MacMine Lab", "Mac is running hot — reducing mining threads.", "thermal_hot"
            )
            if mining_active:
                snap = mining_runner.snapshot()
                if snap.threads and snap.threads > 1:
                    reduction = max(1, int(snap.threads * THERMAL_THREAD_REDUCTION_FRACTION))
                    new_threads = max(1, snap.threads - reduction)
                    if new_threads < snap.threads:
                        mining_runner.restart_with_threads(new_threads, reason="thermal_hot_reduced")
                        self._record_action(f"thermal_hot_reduced_to_{new_threads}_threads")
            # benchmark mode: notification only — see module docstring.

        if mining_active:
            battery = telemetry.battery
            if battery.on_ac_power is False:
                if not settings.allow_mining_on_battery:
                    notifications.send(
                        "MacMine Lab", "Power adapter disconnected — mining stopped.",
                        "battery_ac_disconnected",
                    )
                    mining_runner.stop(reason="battery_ac_disconnected")
                    self._record_action("battery_ac_disconnected_stop")
                elif (
                    battery.percent is not None
                    and battery.percent < settings.battery_pause_threshold_percent
                ):
                    notifications.send(
                        "MacMine Lab",
                        f"Battery below {settings.battery_pause_threshold_percent}% — mining stopped.",
                        "battery_low",
                    )
                    mining_runner.stop(reason="battery_low")
                    self._record_action("battery_low_stop")

    def snapshot(self) -> SafetyState:
        settings = get_settings()
        telemetry = hardware.sample_telemetry()
        with self._lock:
            return SafetyState(
                watching=self._thread is not None and self._thread.is_alive(),
                thermal_state=telemetry.thermal.state,
                on_ac_power=telemetry.battery.on_ac_power,
                battery_percent=telemetry.battery.percent,
                automation_enabled=settings.automation_enabled,
                allow_mining_on_battery=settings.allow_mining_on_battery,
                battery_pause_threshold_percent=settings.battery_pause_threshold_percent,
                last_action=self._last_action,
                last_action_at=self._last_action_at,
            )


safety_manager = SafetyManager()
