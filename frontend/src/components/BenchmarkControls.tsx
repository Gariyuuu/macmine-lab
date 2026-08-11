"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, type BenchmarkLiveState, type HardwareInfo } from "@/lib/api";

const DURATIONS = [
  { value: "30", label: "30 seconds" },
  { value: "60", label: "1 minute" },
  { value: "300", label: "5 minutes" },
] as const;

export function BenchmarkControls({
  hardware,
  benchmark,
}: {
  hardware: HardwareInfo | null;
  benchmark: BenchmarkLiveState | null;
}) {
  const totalCores = hardware?.total_cores ?? 8;
  const [threads, setThreads] = useState(totalCores);
  const [duration, setDuration] = useState<"30" | "60" | "300">("30");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const running = benchmark?.running ?? false;

  async function handleStart() {
    setError(null);
    setPending(true);
    try {
      await api.benchmarkStart(threads, Number(duration) as 30 | 60 | 300);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(false);
    }
  }

  async function handleStop() {
    setError(null);
    setPending(true);
    try {
      await api.minerStop();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">
          Run a RandomX Benchmark
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-xs text-zinc-500">
          Offline benchmark mode — no wallet, no pool, no network. Runs real XMRig RandomX
          hashing for a fixed duration, then stops.
        </p>

        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase tracking-wider text-zinc-500">Threads</label>
            <Select
              value={String(threads)}
              onValueChange={(v) => setThreads(Number(v))}
              disabled={running}
            >
              <SelectTrigger className="w-32 font-mono">
                <SelectValue>{(v: string) => `${v} thread${v === "1" ? "" : "s"}`}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: totalCores }, (_, i) => i + 1).map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    {n} thread{n > 1 ? "s" : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase tracking-wider text-zinc-500">Duration</label>
            <Select
              value={duration}
              onValueChange={(v) => setDuration(v as "30" | "60" | "300")}
              disabled={running}
            >
              <SelectTrigger className="w-36 font-mono">
                <SelectValue>
                  {(v: string) => DURATIONS.find((d) => d.value === v)?.label ?? v}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {DURATIONS.map((d) => (
                  <SelectItem key={d.value} value={d.value}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {!running ? (
            <Button onClick={handleStart} disabled={pending} className="ml-auto">
              {pending ? "Starting…" : "Start Benchmark"}
            </Button>
          ) : (
            <Button
              onClick={handleStop}
              disabled={pending}
              variant="destructive"
              className="ml-auto"
            >
              {pending ? "Stopping…" : "STOP"}
            </Button>
          )}
        </div>

        {running && benchmark && (
          <p className="text-xs text-zinc-500">
            Running: {benchmark.threads} threads, {benchmark.elapsed_s ?? 0}s of{" "}
            {benchmark.duration_target_s}s target.
          </p>
        )}
        {benchmark?.error && (
          <p className="text-xs text-red-400">Last run error: {benchmark.error}</p>
        )}
        {error && <p className="text-xs text-red-400">{error}</p>}
      </CardContent>
    </Card>
  );
}
