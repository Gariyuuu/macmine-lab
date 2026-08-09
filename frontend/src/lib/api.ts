// Thin typed client for the MacMine Lab local backend (Phase 2, ./macmine serve).
// Everything here talks to 127.0.0.1 only — there is no remote backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_MACMINE_API_BASE ?? "http://127.0.0.1:8834";
export const WS_BASE =
  process.env.NEXT_PUBLIC_MACMINE_WS_BASE ?? "ws://127.0.0.1:8834";

export interface HardwareInfo {
  model_name: string | null;
  model_identifier: string | null;
  chip: string | null;
  total_cores: number | null;
  performance_cores: number | null;
  efficiency_cores: number | null;
  ram_gb: number | null;
  macos_version: string | null;
  macos_build: string | null;
  architecture: string;
  is_apple_silicon: boolean;
  is_rosetta_translated: boolean;
}

export interface BatteryInfo {
  present: boolean;
  percent: number | null;
  charging: boolean | null;
  on_ac_power: boolean | null;
  raw_status: string | null;
}

export interface ThermalInfo {
  state: "NORMAL" | "WARM" | "HOT" | "CRITICAL" | "UNAVAILABLE";
  cpu_speed_limit_percent: number | null;
}

export interface CpuLoadInfo {
  user_percent: number | null;
  sys_percent: number | null;
  idle_percent: number | null;
  load_avg_1m: number | null;
  load_avg_5m: number | null;
  load_avg_15m: number | null;
}

export interface MemoryInfo {
  total_bytes: number | null;
  used_gb: number | null;
  unused_gb: number | null;
}

export interface SystemTelemetry {
  battery: BatteryInfo;
  thermal: ThermalInfo;
  cpu: CpuLoadInfo;
  memory: MemoryInfo;
}

export interface MinerStatus {
  running: boolean;
  pid: number | null;
  cpu_percent: number | null;
  started_at: string | null;
}

export interface BenchmarkLiveState {
  running: boolean;
  threads: number | null;
  duration_target_s: number | null;
  elapsed_s: number | null;
  latest_hashrate_10s: number | null;
  latest_hashrate_60s: number | null;
  last_result: BenchmarkResult | null;
  error: string | null;
}

export interface HashrateSample {
  t_offset_s: number;
  hashrate_10s: number | null;
  hashrate_60s: number | null;
}

export interface BenchmarkResult {
  threads: number;
  duration_target_s: number;
  duration_actual_s: number;
  started_at: string;
  ended_at: string;
  xmrig_version: string | null;
  hashrate_samples: HashrateSample[];
  avg_hs: number | null;
  peak_hs: number | null;
  low_hs: number | null;
  hs_per_thread: number | null;
  final_thermal_state: string;
  stopped_reason: string;
}

export interface BenchmarkHistoryEntry {
  id: number;
  threads: number;
  duration_target_s: number;
  duration_actual_s: number;
  started_at: string;
  ended_at: string;
  xmrig_version: string | null;
  avg_hs: number | null;
  peak_hs: number | null;
  low_hs: number | null;
  hs_per_thread: number | null;
  final_thermal_state: string;
  stopped_reason: string;
}

export interface IntegrityRecord {
  installed: number;
  binary_path: string | null;
  version: string | null;
  architecture: string | null;
  sha256: string | null;
  install_source: string;
  upstream_project: string;
  verification_method: string;
  checked_at: string;
}

export interface LiveWsPayload {
  t: number;
  telemetry: SystemTelemetry;
  miner: MinerStatus;
  benchmark: BenchmarkLiveState;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${init?.method ?? "GET"} ${path} -> ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => apiFetch<{ status: string }>("/api/health"),
  hardware: () => apiFetch<HardwareInfo>("/api/hardware"),
  telemetryLive: () =>
    apiFetch<{ telemetry: SystemTelemetry; miner_running: boolean; miner_cpu_percent: number | null }>(
      "/api/telemetry/live"
    ),
  integrity: () => apiFetch<IntegrityRecord>("/api/integrity"),
  minerStatus: () => apiFetch<MinerStatus>("/api/miner/status"),
  minerStop: () => apiFetch<{ stopped: boolean }>("/api/miner/stop", { method: "POST" }),
  benchmarkStart: (threads: number, durationSeconds: 30 | 60 | 300) =>
    apiFetch<{ started: boolean; threads: number; duration_seconds: number }>(
      `/api/benchmark/start?threads=${threads}&duration_seconds=${durationSeconds}`,
      { method: "POST" }
    ),
  benchmarkLive: () => apiFetch<BenchmarkLiveState>("/api/benchmark/live"),
  benchmarkHistory: (limit = 50) =>
    apiFetch<BenchmarkHistoryEntry[]>(`/api/benchmark/history?limit=${limit}`),
  latestLog: (lines = 200) =>
    apiFetch<{ log_file: string | null; lines: string[] }>(`/api/logs/latest?lines=${lines}`),
};
