"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, type HardwareInfo, type MiningLiveState, type Pool, type Wallet } from "@/lib/api";

export function MiningControls({
  hardware,
  mining,
}: {
  hardware: HardwareInfo | null;
  mining: MiningLiveState | null;
}) {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [pools, setPools] = useState<Pool[]>([]);
  const [walletId, setWalletId] = useState<string>("");
  const [poolId, setPoolId] = useState<string>("");
  const [threads, setThreads] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const totalCores = hardware?.total_cores ?? 8;
  const running = mining?.running ?? false;

  useEffect(() => {
    api.listWallets().then((w) => {
      setWallets(w);
      if (w.length > 0) setWalletId(String(w[0].id));
    }).catch(() => {});
    api.listPools().then((p) => {
      setPools(p);
      if (p.length > 0) setPoolId(String(p[0].id));
    }).catch(() => {});
  }, []);

  const effectiveThreads = threads ?? totalCores;

  async function handleStart() {
    if (!walletId || !poolId) return;
    setError(null);
    setPending(true);
    try {
      await api.miningStart(Number(poolId), Number(walletId), effectiveThreads);
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
      await api.miningStop();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(false);
    }
  }

  const notConfigured = wallets.length === 0 || pools.length === 0;

  return (
    <Card className="border-white/10 bg-zinc-900/60">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">Real Mining</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {notConfigured ? (
          <p className="text-xs text-zinc-500">
            No wallet or pool configured yet.{" "}
            <Link href="/setup" className="underline hover:text-zinc-300">
              Set one up
            </Link>{" "}
            to enable real mining.
          </p>
        ) : (
          <>
            <p className="text-xs text-zinc-500">
              Mines real Monero to your configured wallet through your configured pool. This
              generates actual network traffic and, once shares are accepted, real (if tiny)
              mining rewards.
            </p>

            <div className="flex flex-wrap items-end gap-3">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] uppercase tracking-wider text-zinc-500">Wallet</label>
                <Select value={walletId} onValueChange={(v) => setWalletId(v ?? "")} disabled={running}>
                  <SelectTrigger className="w-48">
                    <SelectValue>
                      {(v: string) => {
                        const w = wallets.find((w) => String(w.id) === v);
                        return w ? w.label || `${w.address.slice(0, 10)}…` : v;
                      }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {wallets.map((w) => (
                      <SelectItem key={w.id} value={String(w.id)}>
                        {w.label || `${w.address.slice(0, 10)}…`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] uppercase tracking-wider text-zinc-500">Pool</label>
                <Select value={poolId} onValueChange={(v) => setPoolId(v ?? "")} disabled={running}>
                  <SelectTrigger className="w-48">
                    <SelectValue>
                      {(v: string) => pools.find((p) => String(p.id) === v)?.name ?? v}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {pools.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] uppercase tracking-wider text-zinc-500">Threads</label>
                <Select
                  value={String(effectiveThreads)}
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

              {!running ? (
                <Button onClick={handleStart} disabled={pending} className="ml-auto">
                  {pending ? "Starting…" : "Start Mining"}
                </Button>
              ) : (
                <Button onClick={handleStop} disabled={pending} variant="destructive" className="ml-auto">
                  {pending ? "Stopping…" : "STOP"}
                </Button>
              )}
            </div>

            {running && mining && (
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-zinc-500">
                <span>Pool: {mining.connection_pool ?? "connecting…"}</span>
                <span>
                  Shares: {mining.shares_good ?? 0} accepted / {(mining.shares_total ?? 0) - (mining.shares_good ?? 0)} rejected
                </span>
              </div>
            )}
            {mining?.error && <p className="text-xs text-red-400">Last session error: {mining.error}</p>}
            {error && <p className="text-xs text-red-400">{error}</p>}
          </>
        )}
      </CardContent>
    </Card>
  );
}
