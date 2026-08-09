"""Unit tests for telemetry parsing. Every fixture string below is real
output captured from this machine (see conversation/session notes) — we're
testing that our regexes handle the actual formats macOS emits, not made-up
shapes."""

from unittest.mock import patch

from macmine_lab import hardware

BATT_AC_CHARGED = (
    "Now drawing from 'AC Power'\n"
    " -InternalBattery-0 (id=21233763)\t100%; charged; 0:00 remaining present: true\n"
)

BATT_DISCHARGING = (
    "Now drawing from 'Battery Power'\n"
    " -InternalBattery-0 (id=21233763)\t63%; discharging; 2:14 remaining present: true\n"
)

THERM_NORMAL = (
    "Note: No thermal warning level has been recorded\n"
    "Note: No performance warning level has been recorded\n"
    "Note: No CPU power status has been recorded\n"
)

def _therm_with_speed_limit(percent: int) -> str:
    return (
        f"CPU_Scheduler_Limit\t= {percent}\n"
        "CPU_Available_CPUs\t= 12\n"
        f"CPU_Speed_Limit\t= {percent}\n"
    )

TOP_OUTPUT = (
    "Load Avg: 3.66, 8.63, 9.90 \n"
    "CPU usage: 22.8% user, 16.94% sys, 60.96% idle \n"
    "PhysMem: 23G used (3109M wired, 7905M compressor), 271M unused.\n"
)


def test_battery_ac_charged():
    with patch.object(hardware, "_run", return_value=BATT_AC_CHARGED):
        b = hardware.sample_battery()
    assert b.percent == 100
    assert b.on_ac_power is True
    assert b.charging is True
    assert b.raw_status == "charged"


def test_battery_discharging():
    with patch.object(hardware, "_run", return_value=BATT_DISCHARGING):
        b = hardware.sample_battery()
    assert b.percent == 63
    assert b.on_ac_power is False
    assert b.charging is False
    assert b.raw_status == "discharging"


def test_battery_command_unavailable():
    with patch.object(hardware, "_run", return_value=None):
        b = hardware.sample_battery()
    assert b.present is False
    assert b.percent is None


def test_thermal_normal_when_no_warning_recorded():
    with patch.object(hardware, "_run", return_value=THERM_NORMAL):
        t = hardware.sample_thermal()
    assert t.state == "NORMAL"
    assert t.cpu_speed_limit_percent == 100


def test_thermal_warm_from_speed_limit():
    with patch.object(hardware, "_run", return_value=_therm_with_speed_limit(85)):
        t = hardware.sample_thermal()
    assert t.state == "WARM"
    assert t.cpu_speed_limit_percent == 85


def test_thermal_hot_from_speed_limit():
    with patch.object(hardware, "_run", return_value=_therm_with_speed_limit(70)):
        t = hardware.sample_thermal()
    assert t.state == "HOT"


def test_thermal_critical_from_speed_limit():
    with patch.object(hardware, "_run", return_value=_therm_with_speed_limit(30)):
        t = hardware.sample_thermal()
    assert t.state == "CRITICAL"


def test_thermal_unavailable_when_command_fails():
    with patch.object(hardware, "_run", return_value=None):
        t = hardware.sample_thermal()
    assert t.state == "UNAVAILABLE"
    assert t.cpu_speed_limit_percent is None


def test_cpu_and_memory_parsing():
    with patch.object(hardware, "_run") as mock_run:
        def side_effect(cmd, timeout=5.0):
            if cmd[0] == "top":
                return TOP_OUTPUT
            if cmd == ["sysctl", "-n", "hw.memsize"]:
                return "25769803776\n"
            return None
        mock_run.side_effect = side_effect
        cpu, mem = hardware.sample_cpu_and_memory()

    assert cpu.user_percent == 22.8
    assert cpu.sys_percent == 16.94
    assert cpu.idle_percent == 60.96
    assert cpu.load_avg_1m == 3.66
    assert cpu.load_avg_5m == 8.63
    assert cpu.load_avg_15m == 9.90
    assert mem.used_gb == 23.0
    assert mem.unused_gb == round(271 / 1024, 2)
    assert mem.total_bytes == 25769803776


def test_process_cpu_percent_parses_ps_output():
    with patch.object(hardware, "_run", return_value=" 54.2\n"):
        assert hardware.process_cpu_percent(1234) == 54.2


def test_process_cpu_percent_none_when_pid_gone():
    with patch.object(hardware, "_run", return_value=""):
        assert hardware.process_cpu_percent(999999) is None
