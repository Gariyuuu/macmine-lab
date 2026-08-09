"""MacMine Lab CLI — Phase 1: hardware detection, XMRig install/verify,
real RandomX benchmarking, thread calibration, and STOP.

No real mining, wallets, or pools yet — that's Phase 4. Everything here is
either a real measurement or explicitly labeled as unavailable/not yet run.
"""

from __future__ import annotations

import argparse
import sys

from . import benchmark, hardware, integrity, miner


def _fmt(value, suffix: str = "", none_label: str = "Unavailable") -> str:
    if value is None:
        return none_label
    return f"{value}{suffix}"


def cmd_hardware(_args: argparse.Namespace) -> int:
    hw = hardware.detect_hardware()
    telem = hardware.sample_telemetry()

    print("=== MacMine Lab — Hardware ===")
    print(f"Model:              {_fmt(hw.model_name)} ({_fmt(hw.model_identifier)})")
    print(f"Chip:               {_fmt(hw.chip)}")
    print(f"Architecture:       {hw.architecture}"
          + (" (Rosetta-translated!)" if hw.is_rosetta_translated else ""))
    print(f"Apple Silicon:      {'Yes' if hw.is_apple_silicon else 'No'}")
    print(f"CPU cores:          {_fmt(hw.total_cores)} total "
          f"({_fmt(hw.performance_cores)} performance, {_fmt(hw.efficiency_cores)} efficiency)")
    print(f"RAM:                {_fmt(hw.ram_gb, ' GB')}")
    print(f"macOS:              {_fmt(hw.macos_version)} (build {_fmt(hw.macos_build)})")
    print()
    print("=== Live telemetry ===")
    print(f"CPU usage:          {_fmt(telem.cpu.user_percent, '% user')} / "
          f"{_fmt(telem.cpu.sys_percent, '% sys')} / {_fmt(telem.cpu.idle_percent, '% idle')}")
    print(f"Load average:       {_fmt(telem.cpu.load_avg_1m)} (1m) "
          f"{_fmt(telem.cpu.load_avg_5m)} (5m) {_fmt(telem.cpu.load_avg_15m)} (15m)")
    print(f"Memory:             {_fmt(telem.memory.used_gb, ' GB used')}, "
          f"{_fmt(telem.memory.unused_gb, ' GB unused')}")
    print(f"Battery:            {_fmt(telem.battery.percent, '%')} "
          f"({_fmt(telem.battery.raw_status)})")
    print(f"Power source:       {'AC Power' if telem.battery.on_ac_power else 'Battery'}")
    print(f"Thermal state:      {telem.thermal.state}"
          + (f" (CPU speed limit {telem.thermal.cpu_speed_limit_percent}%)"
             if telem.thermal.cpu_speed_limit_percent is not None else ""))
    return 0


def cmd_setup(_args: argparse.Namespace) -> int:
    print("=== MacMine Lab — Setup ===")
    hw = hardware.detect_hardware()
    if not hw.is_apple_silicon:
        print("WARNING: This Mac does not appear to be Apple Silicon. "
              "MacMine Lab targets Apple Silicon; continuing anyway.")
    if hw.is_rosetta_translated:
        print("WARNING: This process is running under Rosetta translation. "
              "Re-run using a native arm64 terminal/Python for accurate results.")

    print("\nInstalling/checking XMRig via Homebrew...")
    ok, message = integrity.install_xmrig_via_brew()
    print(message)
    if not ok:
        return 1

    print("\nVerifying installed XMRig binary...")
    record = integrity.verify_installed_xmrig()
    integrity.save_integrity_record(record)
    print(f"  Version:      {_fmt(record.version)}")
    print(f"  Architecture: {_fmt(record.architecture)}")
    print(f"  Path:         {_fmt(record.binary_path)}")
    print(f"  SHA-256:      {_fmt(record.sha256)}")
    print(f"  Source:       {record.install_source}")
    print(f"  Method:       {record.verification_method}")

    if not record.installed:
        print("\nXMRig is still not on PATH — setup did not succeed.")
        return 1

    print("\nSetup complete. Try: ./macmine benchmark --duration 30")
    return 0


def cmd_integrity(_args: argparse.Namespace) -> int:
    record = integrity.load_integrity_record()
    if not record:
        print("No integrity record yet. Run `./macmine setup` first.")
        return 1
    print("=== Miner Integrity ===")
    for key, value in record.items():
        print(f"{key:20s} {value}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    hw = hardware.detect_hardware()
    threads = args.threads or hw.total_cores
    if not threads:
        print("Could not detect CPU core count and no --threads given.")
        return 1

    print(f"=== Running {args.duration}s RandomX benchmark @ {threads} threads ===")
    print("(offline benchmark mode — no pool, no network, no wallet involved)\n")
    try:
        result = benchmark.run_benchmark(threads, args.duration)
    except miner.XMRigNotInstalledError as e:
        print(f"Error: {e}")
        return 1
    except miner.XMRigAlreadyRunningError as e:
        print(f"Error: {e}")
        return 1

    print(f"XMRig version:      {_fmt(result.xmrig_version)}")
    print(f"Duration:           {result.duration_actual_s}s (target {result.duration_target_s}s)")
    print(f"Stopped because:    {result.stopped_reason}")
    print(f"Samples collected:  {len(result.hashrate_samples)}")
    print()
    print(f"Average hashrate:   {_fmt(result.avg_hs, ' H/s')}")
    print(f"Peak hashrate:      {_fmt(result.peak_hs, ' H/s')}")
    print(f"Low hashrate:       {_fmt(result.low_hs, ' H/s')}")
    print(f"H/s per thread:     {_fmt(result.hs_per_thread, ' H/s')}")
    print(f"Final thermal state:{result.final_thermal_state:>10s}")
    if result.avg_hs is None:
        print("\nNo hashrate samples were collected — the duration may be too "
              "short relative to RandomX dataset warmup. Try --duration 30 or higher.")
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    hw = hardware.detect_hardware()
    total = hw.total_cores or 8
    candidates = sorted({t for t in (2, 4, 6, 8, 10, 12) if t <= total} | {total})

    print(f"=== Thread calibration ({len(candidates)} configs x {args.duration}s each) ===\n")
    results = []
    for threads in candidates:
        print(f"-- Testing {threads} threads for {args.duration}s...")
        try:
            r = benchmark.run_benchmark(threads, args.duration)
        except (miner.XMRigNotInstalledError, miner.XMRigAlreadyRunningError) as e:
            print(f"Error: {e}")
            return 1
        results.append(r)
        print(f"   avg {_fmt(r.avg_hs, ' H/s')}  "
              f"({_fmt(r.hs_per_thread, ' H/s/thread')})  thermal={r.final_thermal_state}")

    print("\n=== Results ===")
    print(f"{'Threads':>8}  {'Avg H/s':>10}  {'H/s/thread':>12}  {'Thermal':>10}")
    for r in results:
        print(f"{r.threads:>8}  {_fmt(r.avg_hs):>10}  {_fmt(r.hs_per_thread):>12}  "
              f"{r.final_thermal_state:>10}")

    tested = [r for r in results if r.avg_hs is not None]
    if not tested:
        print("\nNo usable results — cannot recommend configs.")
        return 0

    def best_in_range(lo_frac, hi_frac):
        in_range = [r for r in tested if lo_frac <= r.threads / total <= hi_frac]
        if not in_range:
            return None
        return max(in_range, key=lambda r: r.avg_hs)

    eco = best_in_range(0.20, 0.40)
    balanced = best_in_range(0.40, 0.65)
    performance = max(tested, key=lambda r: r.avg_hs)

    print("\n=== Recommended configs (measured, not assumed) ===")
    print(f"Eco:         {eco.threads if eco else 'not tested in range'} threads"
          + (f" ({_fmt(eco.avg_hs, ' H/s')})" if eco else ""))
    print(f"Balanced:    {balanced.threads if balanced else 'not tested in range'} threads"
          + (f" ({_fmt(balanced.avg_hs, ' H/s')})" if balanced else ""))
    print(f"Performance: {performance.threads} threads ({_fmt(performance.avg_hs, ' H/s')})")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    status = miner.get_status()
    if not status.running:
        print("Status: STOPPED — no MacMine-launched xmrig process is running.")
        return 0
    print("Status: RUNNING")
    print(f"  PID:         {status.pid}")
    print(f"  CPU usage:   {_fmt(status.cpu_percent, '%')}")
    print(f"  Started:     {status.started_at}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    print(f"=== MacMine Lab backend — http://127.0.0.1:{args.port} (local only) ===")
    uvicorn.run("macmine_lab.api:app", host="127.0.0.1", port=args.port, log_level="info")
    return 0


def cmd_stop(_args: argparse.Namespace) -> int:
    status = miner.get_status()
    if not status.running:
        print("Nothing to stop — no MacMine-launched xmrig process is running.")
        return 0
    print(f"Stopping xmrig (PID {status.pid})...")
    ok = miner.stop_tracked()
    print("Stopped." if ok else "WARNING: could not confirm the process stopped.")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macmine", description="MacMine Lab")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("hardware", help="Detect hardware and show live telemetry").set_defaults(
        func=cmd_hardware
    )
    sub.add_parser("setup", help="Install/verify XMRig via Homebrew").set_defaults(
        func=cmd_setup
    )
    sub.add_parser("integrity", help="Show recorded miner integrity info").set_defaults(
        func=cmd_integrity
    )

    bench = sub.add_parser("benchmark", help="Run a real, offline RandomX benchmark")
    bench.add_argument("--threads", type=int, default=None, help="CPU threads (default: all)")
    bench.add_argument("--duration", type=int, default=30, choices=[30, 60, 300],
                        help="Benchmark duration in seconds")
    bench.set_defaults(func=cmd_benchmark)

    calib = sub.add_parser("calibrate", help="Benchmark multiple thread counts and recommend configs")
    calib.add_argument("--duration", type=int, default=30, choices=[30, 60],
                        help="Duration per thread config in seconds")
    calib.set_defaults(func=cmd_calibrate)

    serve = sub.add_parser("serve", help="Run the local backend API (127.0.0.1 only)")
    serve.add_argument("--port", type=int, default=8834)
    serve.set_defaults(func=cmd_serve)

    sub.add_parser("status", help="Show whether xmrig is running").set_defaults(func=cmd_status)
    sub.add_parser("stop", help="Stop any MacMine-launched xmrig process").set_defaults(
        func=cmd_stop
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
