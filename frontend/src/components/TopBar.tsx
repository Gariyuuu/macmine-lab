"use client";

import type { ConnectionState } from "@/lib/useLiveSocket";
import type { HardwareInfo } from "@/lib/api";

export function TopBar({
  hardware,
  connection,
  benchmarkRunning,
}: {
  hardware: HardwareInfo | null;
  connection: ConnectionState;
  benchmarkRunning: boolean;
}) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 px-6 py-4">
      <div className="flex items-center gap-3">
        <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
        <span className="text-xs text-zinc-500">Phase 3 · Benchmark Mode</span>
      </div>

      <div className="flex flex-wrap items-center gap-6 text-sm">
        <Stat label="CHIP" value={hardware?.chip ?? "Detecting…"} />
        <Stat
          label="STATUS"
          value={benchmarkRunning ? "BENCHMARKING" : "IDLE"}
          dotClassName={benchmarkRunning ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}
        />
        <Stat
          label="BACKEND"
          value={
            connection === "open" ? "Connected" : connection === "connecting" ? "Connecting…" : "Disconnected"
          }
          dotClassName={
            connection === "open" ? "bg-emerald-400" : connection === "connecting" ? "bg-amber-400" : "bg-red-500"
          }
        />
      </div>
    </header>
  );
}

function Stat({ label, value, dotClassName }: { label: string; value: string; dotClassName?: string }) {
  return (
    <div className="flex items-center gap-2">
      {dotClassName && <span className={`h-2 w-2 rounded-full ${dotClassName}`} />}
      <div className="flex flex-col leading-tight">
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</span>
        <span className="font-mono text-zinc-200">{value}</span>
      </div>
    </div>
  );
}
