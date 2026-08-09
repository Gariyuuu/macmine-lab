"use client";

import Link from "next/link";
import type { ConnectionState } from "@/lib/useLiveSocket";
import type { HardwareInfo } from "@/lib/api";

export type ActivityStatus = "MINING" | "BENCHMARKING" | "IDLE";

export function TopBar({
  hardware,
  connection,
  status,
}: {
  hardware: HardwareInfo | null;
  connection: ConnectionState;
  status: ActivityStatus;
}) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 px-6 py-4">
      <div className="flex items-center gap-3">
        <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
        <span className="text-xs text-zinc-500">Phase 6</span>
      </div>

      <div className="flex flex-wrap items-center gap-6 text-sm">
        <Stat label="CHIP" value={hardware?.chip ?? "Detecting…"} />
        <Stat
          label="STATUS"
          value={status}
          dotClassName={
            status === "MINING"
              ? "bg-red-400 animate-pulse"
              : status === "BENCHMARKING"
                ? "bg-emerald-400 animate-pulse"
                : "bg-zinc-600"
          }
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
        <nav className="flex items-center gap-4 text-xs text-zinc-500">
          <Link href="/journal" className="hover:text-zinc-200">
            Journal
          </Link>
          <Link href="/analytics" className="hover:text-zinc-200">
            Analytics
          </Link>
          <Link href="/earnings" className="hover:text-zinc-200">
            Earnings
          </Link>
          <Link href="/first-penny" className="hover:text-zinc-200">
            First Penny
          </Link>
          <Link href="/setup" className="hover:text-zinc-200">
            Setup →
          </Link>
        </nav>
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
