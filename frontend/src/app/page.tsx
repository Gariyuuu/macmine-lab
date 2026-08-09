"use client";

import { useEffect, useRef, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { HeroMetric } from "@/components/HeroMetric";
import { HashrateChart, type ChartPoint } from "@/components/HashrateChart";
import { SystemHealthPanel } from "@/components/SystemHealthPanel";
import { BenchmarkControls } from "@/components/BenchmarkControls";
import { LogTerminal } from "@/components/LogTerminal";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLiveSocket } from "@/lib/useLiveSocket";
import { api, type BenchmarkHistoryEntry, type HardwareInfo, type LiveWsPayload } from "@/lib/api";
import { formatHashrate, formatTimeAgo } from "@/lib/format";

export default function Dashboard() {
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [history, setHistory] = useState<BenchmarkHistoryEntry[]>([]);
  const [chartPoints, setChartPoints] = useState<ChartPoint[]>([]);
  const wasRunning = useRef(false);

  useEffect(() => {
    api.hardware().then(setHardware).catch(() => {});
    api.benchmarkHistory(10).then(setHistory).catch(() => {});
  }, []);

  // Runs inside the WebSocket's own onmessage callback (see useLiveSocket) —
  // a real external-system subscription, not a useEffect reacting to state.
  function handlePayload(payload: LiveWsPayload) {
    const running = payload.benchmark.running;

    if (running && !wasRunning.current) {
      setChartPoints([]);
    }
    if (!running && wasRunning.current) {
      api.benchmarkHistory(10).then(setHistory).catch(() => {});
    }
    wasRunning.current = running;

    if (running && payload.benchmark.elapsed_s !== null && payload.benchmark.latest_hashrate_10s !== null) {
      const t = payload.benchmark.elapsed_s;
      const hs = payload.benchmark.latest_hashrate_10s;
      setChartPoints((prev) => {
        if (prev.length > 0 && prev[prev.length - 1].t === t) return prev;
        return [...prev, { t, hs }].slice(-300);
      });
    }
  }

  const { payload, state: connection } = useLiveSocket(handlePayload);
  const benchmark = payload?.benchmark ?? null;

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <TopBar hardware={hardware} connection={connection} benchmarkRunning={benchmark?.running ?? false} />

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-8">
        <Card className="border-white/10 bg-zinc-900/60">
          <CardContent>
            <HeroMetric benchmark={benchmark} lastRun={history[0] ?? null} />
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-zinc-900/60">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zinc-400">Live Hashrate</CardTitle>
          </CardHeader>
          <CardContent>
            <HashrateChart points={chartPoints} />
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <SystemHealthPanel telemetry={payload?.telemetry ?? null} miner={payload?.miner ?? null} />
          <BenchmarkControls hardware={hardware} benchmark={benchmark} />
        </div>

        <LogTerminal active={benchmark?.running ?? false} />

        {history.length > 0 && (
          <Card className="border-white/10 bg-zinc-900/60">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400">Recent Benchmark Runs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px] font-mono text-xs">
                  <thead className="text-zinc-500">
                    <tr className="text-left">
                      <th className="pb-2 pr-4 font-normal">When</th>
                      <th className="pb-2 pr-4 font-normal">Threads</th>
                      <th className="pb-2 pr-4 font-normal">Avg</th>
                      <th className="pb-2 pr-4 font-normal">Peak</th>
                      <th className="pb-2 pr-4 font-normal">H/s per thread</th>
                      <th className="pb-2 font-normal">Thermal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((run) => (
                      <tr key={run.id} className="border-t border-white/5 text-zinc-300">
                        <td className="py-2 pr-4 text-zinc-500">{formatTimeAgo(run.started_at)}</td>
                        <td className="py-2 pr-4">{run.threads}</td>
                        <td className="py-2 pr-4">{formatHashrate(run.avg_hs)}</td>
                        <td className="py-2 pr-4">{formatHashrate(run.peak_hs)}</td>
                        <td className="py-2 pr-4">{formatHashrate(run.hs_per_thread)}</td>
                        <td className="py-2">{run.final_thermal_state}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </main>

      <footer className="border-t border-white/10 px-6 py-4 text-center text-xs text-zinc-600">
        Everything on this page runs locally on this Mac. No wallet, no pool, no network mining
        yet — that&apos;s Phase 4.
      </footer>
    </div>
  );
}
