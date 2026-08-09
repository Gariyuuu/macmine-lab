"""Hardware detection and live system telemetry for Apple Silicon Macs.

Every value here comes from a real macOS command (system_profiler, sysctl,
pmset, top). If a command doesn't expose something, the field is left as
None — callers must render that as "Unavailable", never a guess.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from dataclasses import dataclass, field


def _run(cmd: list[str], timeout: float = 5.0) -> str | None:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return result.stdout
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


@dataclass
class HardwareInfo:
    model_name: str | None
    model_identifier: str | None
    chip: str | None
    total_cores: int | None
    performance_cores: int | None
    efficiency_cores: int | None
    ram_gb: float | None
    macos_version: str | None
    macos_build: str | None
    architecture: str
    is_apple_silicon: bool
    is_rosetta_translated: bool


@dataclass
class BatteryInfo:
    present: bool
    percent: int | None
    charging: bool | None
    on_ac_power: bool | None
    raw_status: str | None  # e.g. "charged", "charging", "discharging"


@dataclass
class ThermalInfo:
    state: str  # NORMAL | WARM | HOT | CRITICAL | UNAVAILABLE
    cpu_speed_limit_percent: int | None
    raw_fields: dict = field(default_factory=dict)


@dataclass
class CpuLoadInfo:
    user_percent: float | None
    sys_percent: float | None
    idle_percent: float | None
    load_avg_1m: float | None
    load_avg_5m: float | None
    load_avg_15m: float | None


@dataclass
class MemoryInfo:
    total_bytes: int | None
    used_gb: float | None
    unused_gb: float | None


@dataclass
class SystemTelemetry:
    battery: BatteryInfo
    thermal: ThermalInfo
    cpu: CpuLoadInfo
    memory: MemoryInfo


def _detect_architecture() -> tuple[str, bool, bool]:
    machine = platform.machine()
    is_arm = machine == "arm64"
    # If we're arm64, we're native. If we're x86_64 on an ARM Mac we'd be
    # under Rosetta, but sysctl.proc_translated tells us definitively.
    translated_raw = _run(["sysctl", "-n", "sysctl.proc_translated"])
    is_translated = bool(translated_raw and translated_raw.strip() == "1")
    return machine, is_arm, is_translated


def detect_hardware() -> HardwareInfo:
    machine, is_arm, is_translated = _detect_architecture()

    model_name = None
    model_identifier = None
    chip = None
    ram_gb = None
    sp_raw = _run(["system_profiler", "SPHardwareDataType", "-json"])
    if sp_raw:
        try:
            data = json.loads(sp_raw)
            overview = data.get("SPHardwareDataType", [{}])[0]
            model_name = overview.get("machine_name")
            model_identifier = overview.get("machine_model")
            chip = overview.get("chip_type")
            mem_str = overview.get("physical_memory", "")
            match = re.match(r"([\d.]+)\s*GB", mem_str)
            if match:
                ram_gb = float(match.group(1))
        except (json.JSONDecodeError, IndexError, KeyError):
            pass

    total_cores = None
    perf_cores = None
    eff_cores = None
    ncpu_raw = _run(["sysctl", "-n", "hw.ncpu"])
    if ncpu_raw and ncpu_raw.strip().isdigit():
        total_cores = int(ncpu_raw.strip())
    perf_raw = _run(["sysctl", "-n", "hw.perflevel0.physicalcpu"])
    if perf_raw and perf_raw.strip().isdigit():
        perf_cores = int(perf_raw.strip())
    eff_raw = _run(["sysctl", "-n", "hw.perflevel1.physicalcpu"])
    if eff_raw and eff_raw.strip().isdigit():
        eff_cores = int(eff_raw.strip())

    if ram_gb is None:
        memsize_raw = _run(["sysctl", "-n", "hw.memsize"])
        if memsize_raw and memsize_raw.strip().isdigit():
            ram_gb = round(int(memsize_raw.strip()) / (1024**3), 1)

    macos_version = None
    macos_build = None
    sw_vers_raw = _run(["sw_vers"])
    if sw_vers_raw:
        v_match = re.search(r"ProductVersion:\s*(\S+)", sw_vers_raw)
        b_match = re.search(r"BuildVersion:\s*(\S+)", sw_vers_raw)
        if v_match:
            macos_version = v_match.group(1)
        if b_match:
            macos_build = b_match.group(1)

    return HardwareInfo(
        model_name=model_name,
        model_identifier=model_identifier,
        chip=chip,
        total_cores=total_cores,
        performance_cores=perf_cores,
        efficiency_cores=eff_cores,
        ram_gb=ram_gb,
        macos_version=macos_version,
        macos_build=macos_build,
        architecture=machine,
        is_apple_silicon=is_arm or is_translated,
        is_rosetta_translated=is_translated,
    )


def sample_battery() -> BatteryInfo:
    raw = _run(["pmset", "-g", "batt"])
    if not raw:
        return BatteryInfo(
            present=False, percent=None, charging=None, on_ac_power=None, raw_status=None
        )

    on_ac_power = "'AC Power'" in raw
    percent_match = re.search(r"(\d+)%", raw)
    percent = int(percent_match.group(1)) if percent_match else None

    status_match = re.search(r"%;\s*([a-zA-Z ]+);", raw)
    raw_status = status_match.group(1).strip() if status_match else None

    present = "present: true" in raw
    charging = None
    if raw_status:
        charging = raw_status in ("charging", "charged")

    return BatteryInfo(
        present=present,
        percent=percent,
        charging=charging,
        on_ac_power=on_ac_power,
        raw_status=raw_status,
    )


def sample_thermal() -> ThermalInfo:
    raw = _run(["pmset", "-g", "therm"])
    if not raw:
        return ThermalInfo(state="UNAVAILABLE", cpu_speed_limit_percent=None)

    if "No thermal warning level has been recorded" in raw:
        return ThermalInfo(state="NORMAL", cpu_speed_limit_percent=100)

    fields = {}
    for line in raw.splitlines():
        kv_match = re.match(r"\s*(\w+)\s*=\s*(\d+)", line)
        if kv_match:
            fields[kv_match.group(1)] = int(kv_match.group(2))

    speed_limit = fields.get("CPU_Speed_Limit")
    if speed_limit is None:
        state = "NORMAL"
    elif speed_limit >= 100:
        state = "NORMAL"
    elif speed_limit >= 80:
        state = "WARM"
    elif speed_limit >= 50:
        state = "HOT"
    else:
        state = "CRITICAL"

    return ThermalInfo(state=state, cpu_speed_limit_percent=speed_limit, raw_fields=fields)


def sample_cpu_and_memory() -> tuple[CpuLoadInfo, MemoryInfo]:
    raw = _run(["top", "-l", "1", "-n", "0"], timeout=10.0)
    if not raw:
        return (
            CpuLoadInfo(None, None, None, None, None, None),
            MemoryInfo(None, None, None),
        )

    load_match = re.search(
        r"Load Avg:\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)", raw
    )
    cpu_match = re.search(
        r"CPU usage:\s*([\d.]+)% user,\s*([\d.]+)% sys,\s*([\d.]+)% idle", raw
    )

    cpu_info = CpuLoadInfo(
        user_percent=float(cpu_match.group(1)) if cpu_match else None,
        sys_percent=float(cpu_match.group(2)) if cpu_match else None,
        idle_percent=float(cpu_match.group(3)) if cpu_match else None,
        load_avg_1m=float(load_match.group(1)) if load_match else None,
        load_avg_5m=float(load_match.group(2)) if load_match else None,
        load_avg_15m=float(load_match.group(3)) if load_match else None,
    )

    total_bytes = None
    memsize_raw = _run(["sysctl", "-n", "hw.memsize"])
    if memsize_raw and memsize_raw.strip().isdigit():
        total_bytes = int(memsize_raw.strip())

    used_gb = None
    unused_gb = None
    mem_match = re.search(
        r"PhysMem:\s*([\d.]+)([GM])\s*used.*?([\d.]+)([GM])\s*unused", raw
    )
    if mem_match:
        used_val, used_unit, unused_val, unused_unit = mem_match.groups()
        used_gb = round(float(used_val) / (1024 if used_unit == "M" else 1), 2)
        unused_gb = round(float(unused_val) / (1024 if unused_unit == "M" else 1), 2)

    mem_info = MemoryInfo(total_bytes=total_bytes, used_gb=used_gb, unused_gb=unused_gb)
    return cpu_info, mem_info


def sample_telemetry() -> SystemTelemetry:
    battery = sample_battery()
    thermal = sample_thermal()
    cpu, memory = sample_cpu_and_memory()
    return SystemTelemetry(battery=battery, thermal=thermal, cpu=cpu, memory=memory)


def process_cpu_percent(pid: int) -> float | None:
    """CPU% for a specific PID, e.g. the running xmrig process."""
    raw = _run(["ps", "-o", "%cpu=", "-p", str(pid)])
    if not raw or not raw.strip():
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None
