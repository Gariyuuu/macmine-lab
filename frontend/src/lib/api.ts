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

export interface AddressValidation {
  valid: boolean;
  kind: "standard" | "subaddress" | "integrated" | null;
  reason: string | null;
}

export interface Wallet {
  id: number;
  address: string;
  label: string | null;
  address_kind: string;
  created_at: string;
}

export interface Pool {
  id: number;
  name: string;
  host: string;
  port: number;
  tls: number; // sqlite boolean
  worker_name: string | null;
  password: string | null;
  notes: string | null;
  created_at: string;
}

export interface PoolConnectionTestResult {
  success: boolean;
  latency_ms: number | null;
  message: string;
}

export interface MiningLiveState {
  running: boolean;
  pool_id: number | null;
  wallet_id: number | null;
  threads: number | null;
  session_id: number | null;
  elapsed_s: number | null;
  latest_hashrate_10s: number | null;
  latest_hashrate_60s: number | null;
  shares_good: number | null;
  shares_total: number | null;
  connection_pool: string | null;
  last_result: MiningSessionResult | null;
  error: string | null;
}

export interface MiningSessionResult {
  session_id: number;
  pool_id: number;
  wallet_id: number;
  threads: number;
  started_at: string;
  ended_at: string;
  duration_s: number;
  avg_hs: number | null;
  peak_hs: number | null;
  shares_good: number | null;
  shares_total: number | null;
  hashes_total: number | null;
  stopped_reason: string;
}

export interface MiningHistoryEntry {
  id: number;
  pool_id: number;
  wallet_id: number;
  threads: number;
  started_at: string;
  ended_at: string | null;
  duration_s: number | null;
  avg_hs: number | null;
  peak_hs: number | null;
  shares_good: number | null;
  shares_total: number | null;
  hashes_total: number | null;
  stopped_reason: string | null;
}

export interface PriceSnapshot {
  price_usd: number;
  source: string;
  fetched_at: string;
}

export interface NetworkSnapshot {
  difficulty: number;
  network_hash_rate: number;
  block_reward_xmr: number;
  block_time_s: number;
  height: number;
  source: string;
  fetched_at: string;
}

export interface EconomicsSettings {
  electricity_rate_usd_per_kwh: number | null;
  power_draw_watts: number | null;
}

export interface EarningsEstimate {
  my_hashrate_hs: number;
  network_hash_rate: number;
  my_share_of_network: number;
  xmr_per_hour: number;
  xmr_per_day: number;
  usd_per_hour: number;
  usd_per_day: number;
  power_draw_watts: number | null;
  electricity_rate_usd_per_kwh: number | null;
  electricity_cost_per_day_usd: number | null;
  net_usd_per_day: number | null;
  price_usd: number;
  price_source: string;
  price_fetched_at: string;
  network_source: string;
  network_fetched_at: string;
  network_height: number;
}

export interface Achievement {
  key: string;
  icon: string;
  name: string;
  description: string;
  unavailable?: boolean;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface FirstPennyState {
  estimated_usd_total: number;
  target_usd: number;
  next_milestone_usd: number | null;
  progress_to_next_milestone: number;
  total_hashes: number;
  total_shares_good: number;
  total_shares_total: number;
  total_mining_seconds: number;
  estimate_basis: string;
  achievements: Achievement[];
}

export interface SafetyStatus {
  watching: boolean;
  thermal_state: ThermalInfo["state"];
  on_ac_power: boolean | null;
  battery_percent: number | null;
  automation_enabled: boolean;
  allow_mining_on_battery: boolean;
  battery_pause_threshold_percent: number;
  last_action: string | null;
  last_action_at: string | null;
}

export interface SafetySettings {
  automation_enabled: boolean;
  allow_mining_on_battery: boolean;
  battery_pause_threshold_percent: number;
}

export interface JournalRun extends BenchmarkHistoryEntry {
  result_label: string;
}

export interface CalibrationRecommendation {
  threads: number | null;
  avg_hs: number | null;
  tested: boolean;
}

export interface JournalResponse {
  runs: JournalRun[];
  recommendations: {
    eco: CalibrationRecommendation;
    balanced: CalibrationRecommendation;
    performance: CalibrationRecommendation;
  };
}

export interface AnalyticsSeries {
  available: boolean;
  reason: string | null;
  points: { x: number | string; y: number; label: string | null }[];
}

export interface AnalyticsResponse {
  threads_vs_hashrate: AnalyticsSeries;
  threads_vs_efficiency: AnalyticsSeries;
  session_duration_vs_hashrate: AnalyticsSeries;
  thermal_state_vs_hashrate: AnalyticsSeries;
}

export interface P2PoolDefaults {
  monerod_data_dir: string;
  monerod_rpc_port: number;
  monerod_zmq_port: number;
  monerod_p2p_port: number;
  p2pool_data_dir: string;
  p2pool_stratum_port: number;
}

export interface P2PoolRequirements {
  pruned_gb_low: number;
  pruned_gb_high: number;
  full_gb_low: number;
  full_gb_high: number;
  sources: string[];
  note: string;
}

export interface BinaryIntegrity {
  installed: boolean;
  binary_path: string | null;
  version: string | null;
  architecture: string | null;
  sha256: string | null;
  install_source: string;
  upstream_project: string;
  verification_method: string;
  checked_at: string;
}

export interface MonerodStatus {
  running: boolean;
  pid: number | null;
  height: number | null;
  target_height: number | null;
  synchronized: boolean | null;
  sync_progress_percent: number | null;
  database_size_gb: number | null;
  free_space_gb: number | null;
}

export interface P2PoolProcessStatus {
  running: boolean;
  pid: number | null;
  stratum_port: number | null;
}

export interface LiveWsPayload {
  t: number;
  telemetry: SystemTelemetry;
  miner: MinerStatus;
  benchmark: BenchmarkLiveState;
  mining: MiningLiveState;
  safety: SafetyStatus;
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

  validateWallet: (address: string) =>
    apiFetch<AddressValidation>("/api/wallets/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
    }),
  createWallet: (address: string, label?: string) =>
    apiFetch<Wallet>("/api/wallets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, label: label ?? null }),
    }),
  listWallets: () => apiFetch<Wallet[]>("/api/wallets"),
  deleteWallet: (id: number) => apiFetch<{ deleted: boolean }>(`/api/wallets/${id}`, { method: "DELETE" }),

  createPool: (pool: {
    name: string; host: string; port: number; tls: boolean;
    worker_name?: string | null; password?: string | null; notes?: string | null;
  }) =>
    apiFetch<Pool>("/api/pools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pool),
    }),
  listPools: () => apiFetch<Pool[]>("/api/pools"),
  deletePool: (id: number) => apiFetch<{ deleted: boolean }>(`/api/pools/${id}`, { method: "DELETE" }),
  testPoolConnection: (host: string, port: number, tls: boolean) =>
    apiFetch<PoolConnectionTestResult>("/api/pools/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host, port, tls }),
    }),

  miningStart: (poolId: number, walletId: number, threads: number) =>
    apiFetch<{ started: boolean }>("/api/mining/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pool_id: poolId, wallet_id: walletId, threads }),
    }),
  miningStop: () => apiFetch<{ stopping: boolean }>("/api/mining/stop", { method: "POST" }),
  miningLive: () => apiFetch<MiningLiveState>("/api/mining/live"),
  miningHistory: (limit = 50) => apiFetch<MiningHistoryEntry[]>(`/api/mining/history?limit=${limit}`),

  price: () => apiFetch<PriceSnapshot>("/api/economics/price"),
  network: () => apiFetch<NetworkSnapshot>("/api/economics/network"),
  economicsSettings: () => apiFetch<EconomicsSettings>("/api/economics/settings"),
  setEconomicsSettings: (settings: Partial<EconomicsSettings>) =>
    apiFetch<EconomicsSettings>("/api/economics/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    }),
  estimateEarnings: (hashrateHs: number) =>
    apiFetch<EarningsEstimate>(`/api/economics/estimate?hashrate_hs=${hashrateHs}`),
  firstPenny: () => apiFetch<FirstPennyState>("/api/first-penny"),

  safetyStatus: () => apiFetch<SafetyStatus>("/api/safety/status"),
  safetySettings: () => apiFetch<SafetySettings>("/api/safety/settings"),
  setSafetySettings: (settings: {
    safety_automation_enabled?: boolean;
    allow_mining_on_battery?: boolean;
    battery_pause_threshold_percent?: number;
  }) =>
    apiFetch<SafetySettings>("/api/safety/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    }),

  journal: (limit = 100) => apiFetch<JournalResponse>(`/api/journal?limit=${limit}`),
  analytics: () => apiFetch<AnalyticsResponse>("/api/analytics"),

  p2poolDefaults: () => apiFetch<P2PoolDefaults>("/api/p2pool/defaults"),
  p2poolRequirements: () => apiFetch<P2PoolRequirements>("/api/p2pool/requirements"),

  monerodIntegrity: () => apiFetch<BinaryIntegrity>("/api/p2pool/monerod/integrity"),
  monerodInstall: () => apiFetch<{ installed: boolean; message: string }>("/api/p2pool/monerod/install", { method: "POST" }),
  monerodStatus: () => apiFetch<MonerodStatus>("/api/p2pool/monerod/status"),
  monerodStart: (dataDir: string, pruned: boolean, bandwidthLimitKbps: number | null) =>
    apiFetch<{ started: boolean; pid: number }>("/api/p2pool/monerod/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data_dir: dataDir, pruned, bandwidth_limit_kbps: bandwidthLimitKbps }),
    }),
  monerodStop: () => apiFetch<{ stopped: boolean }>("/api/p2pool/monerod/stop", { method: "POST" }),

  p2poolIntegrity: () => apiFetch<BinaryIntegrity>("/api/p2pool/p2pool/integrity"),
  p2poolInstall: () => apiFetch<{ installed: boolean; message: string }>("/api/p2pool/p2pool/install", { method: "POST" }),
  p2poolStatus: () => apiFetch<P2PoolProcessStatus>("/api/p2pool/p2pool/status"),
  p2poolStart: (walletId: number, mode: "main" | "mini" | "nano", dataDir: string, stratumPort: number, lightMode: boolean) =>
    apiFetch<{ started: boolean; pid: number; stratum_port: number }>("/api/p2pool/p2pool/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ wallet_id: walletId, mode, data_dir: dataDir, stratum_port: stratumPort, light_mode: lightMode }),
    }),
  p2poolStop: () => apiFetch<{ stopped: boolean }>("/api/p2pool/p2pool/stop", { method: "POST" }),
};
