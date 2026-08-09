import { formatHashrate } from "@/lib/format";
import type { BenchmarkLiveState, BenchmarkHistoryEntry } from "@/lib/api";

export function HeroMetric({
  benchmark,
  lastRun,
}: {
  benchmark: BenchmarkLiveState | null;
  lastRun: BenchmarkHistoryEntry | null;
}) {
  const isRunning = benchmark?.running ?? false;
  const value = isRunning ? benchmark?.latest_hashrate_10s : lastRun?.avg_hs;
  const label = isRunning
    ? "LIVE HASHRATE — 10s WINDOW"
    : lastRun
      ? "LAST BENCHMARK AVERAGE"
      : "NO BENCHMARK RUN YET";

  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10">
      <div className="font-mono text-6xl font-semibold tracking-tight tabular-nums sm:text-7xl">
        {isRunning && value === null ? (
          <span className="text-3xl text-zinc-500">warming up RandomX dataset…</span>
        ) : (
          formatHashrate(value)
        )}
      </div>
      <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">{label}</div>
      {!isRunning && !lastRun && (
        <p className="mt-2 max-w-sm text-center text-sm text-zinc-500">
          Run a benchmark below to see real RandomX hashing on this Mac. No wallet or pool
          involved — this is offline benchmark mode.
        </p>
      )}
    </div>
  );
}
