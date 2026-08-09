import { formatHashrate } from "@/lib/format";
import type { BenchmarkLiveState, BenchmarkHistoryEntry, MiningLiveState } from "@/lib/api";

export function HeroMetric({
  mining,
  benchmark,
  lastRun,
}: {
  mining: MiningLiveState | null;
  benchmark: BenchmarkLiveState | null;
  lastRun: BenchmarkHistoryEntry | null;
}) {
  const isMining = mining?.running ?? false;
  const isBenchmarking = !isMining && (benchmark?.running ?? false);

  const value = isMining
    ? mining?.latest_hashrate_10s
    : isBenchmarking
      ? benchmark?.latest_hashrate_10s
      : lastRun?.avg_hs;

  const label = isMining
    ? "LIVE HASHRATE — MINING"
    : isBenchmarking
      ? "LIVE HASHRATE — 10s WINDOW"
      : lastRun
        ? "LAST BENCHMARK AVERAGE"
        : "NO BENCHMARK RUN YET";

  const warmingUp = (isMining || isBenchmarking) && value === null;

  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10">
      <div className="font-mono text-6xl font-semibold tracking-tight tabular-nums sm:text-7xl">
        {warmingUp ? (
          <span className="text-3xl text-zinc-500">
            {isMining ? "connecting to pool…" : "warming up RandomX dataset…"}
          </span>
        ) : (
          formatHashrate(value)
        )}
      </div>
      <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">{label}</div>

      {isMining && mining && (
        <div className="mt-1 flex gap-4 text-sm text-zinc-400">
          <span className="text-emerald-400">{mining.shares_good ?? 0} accepted</span>
          <span className="text-red-400">
            {(mining.shares_total ?? 0) - (mining.shares_good ?? 0)} rejected
          </span>
        </div>
      )}

      {!isMining && !isBenchmarking && !lastRun && (
        <p className="mt-2 max-w-sm text-center text-sm text-zinc-500">
          Run a benchmark below to see real RandomX hashing on this Mac, or set up a wallet and
          pool to start real mining.
        </p>
      )}
    </div>
  );
}
