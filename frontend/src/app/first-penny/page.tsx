"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type FirstPennyState } from "@/lib/api";

const MILESTONES = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0];

export default function FirstPennyPage() {
  const [state, setState] = useState<FirstPennyState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.firstPenny().then(setState).catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">First Penny</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">First Penny Challenge</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Earn an estimated $0.01 from real mining. Progress here is an{" "}
            <strong className="text-zinc-300">estimate</strong>, not a real balance — MacMine Lab has
            no wallet or pool-balance integration in this version, so it can&apos;t confirm an actual
            payout. See &quot;How this is calculated&quot; below.
          </p>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        {state && (
          <>
            <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
              <CardContent className="flex flex-col items-center gap-3 py-8">
                <div className="font-mono text-5xl tabular-nums">
                  ${state.estimated_usd_total.toFixed(4)}
                </div>
                <div className="text-xs uppercase tracking-widest text-zinc-500">
                  estimated earnings (all-time)
                </div>
                <div className="mt-2 flex w-full max-w-md items-center gap-3">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{ width: `${Math.min(state.progress_to_next_milestone * 100, 100)}%` }}
                    />
                  </div>
                  <span className="font-mono text-xs text-zinc-500">
                    {state.next_milestone_usd ? `$${state.next_milestone_usd.toFixed(2)}` : "all milestones hit"}
                  </span>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <StatBox label="Real hashes (all-time)" value={state.total_hashes.toLocaleString()} />
              <StatBox
                label="Real accepted shares"
                value={state.total_shares_good.toLocaleString()}
              />
              <StatBox
                label="Real mining time"
                value={formatDuration(state.total_mining_seconds)}
              />
            </div>

            <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-zinc-400">Achievements</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                {state.achievements.map((a) => (
                  <div
                    key={a.key}
                    className={`flex items-start gap-3 rounded-lg border p-3 ${
                      a.unlocked
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-white/5 bg-black/20 opacity-60"
                    }`}
                  >
                    <span className="text-xl">{a.icon}</span>
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{a.name}</span>
                        {a.unlocked && (
                          <Badge variant="outline" className="border-emerald-500/30 text-emerald-400">
                            Unlocked
                          </Badge>
                        )}
                        {a.unavailable && !a.unlocked && (
                          <Badge variant="outline" className="border-zinc-700 text-zinc-500">
                            Not available yet
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-zinc-500">{a.description}</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-zinc-400">Milestones</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                {MILESTONES.map((m) => (
                  <div
                    key={m}
                    className={`rounded-full border px-3 py-1 font-mono text-xs ${
                      state.estimated_usd_total >= m
                        ? "border-emerald-500/30 text-emerald-400"
                        : "border-zinc-700 text-zinc-500"
                    }`}
                  >
                    ${m.toFixed(2)}
                  </div>
                ))}
              </CardContent>
            </Card>

            <details className="rounded-lg border border-white/10 bg-zinc-900/40 p-4 text-xs text-zinc-500">
              <summary className="cursor-pointer text-zinc-400">How this is calculated</summary>
              <p className="mt-2">{state.estimate_basis}</p>
              <p className="mt-2">
                Real, measured facts (never estimated): total hashes attempted, total shares accepted
                by a pool, total real mining time. The dollar figure is calculated from those real
                hashrate/duration measurements combined with current XMR price and network
                difficulty — it is not a pool balance or a wallet balance, and MacMine Lab has no way
                to verify either of those in this version.
              </p>
            </details>
          </>
        )}
      </main>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardContent className="flex flex-col gap-1 py-4">
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</span>
        <span className="font-mono text-lg">{value}</span>
      </CardContent>
    </Card>
  );
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}
