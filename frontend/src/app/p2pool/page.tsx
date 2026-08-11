"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  api,
  type BinaryIntegrity,
  type MonerodStatus,
  type P2PoolDefaults,
  type P2PoolProcessStatus,
  type P2PoolRequirements,
  type Wallet,
} from "@/lib/api";

const POLL_MS = 5000;

export default function P2PoolPage() {
  const [defaults, setDefaults] = useState<P2PoolDefaults | null>(null);
  const [requirements, setRequirements] = useState<P2PoolRequirements | null>(null);
  const [wallets, setWallets] = useState<Wallet[]>([]);

  const [monerodIntegrity, setMonerodIntegrity] = useState<BinaryIntegrity | null>(null);
  const [monerodStatus, setMonerodStatus] = useState<MonerodStatus | null>(null);
  const [monerodBusy, setMonerodBusy] = useState(false);
  const [monerodError, setMonerodError] = useState<string | null>(null);
  const [confirmingSync, setConfirmingSync] = useState(false);
  const [understandsSync, setUnderstandsSync] = useState(false);
  const [pruned, setPruned] = useState(true);
  const [bandwidthLimit, setBandwidthLimit] = useState("2048");

  const [p2poolIntegrity, setP2poolIntegrity] = useState<BinaryIntegrity | null>(null);
  const [p2poolStatus, setP2poolStatus] = useState<P2PoolProcessStatus | null>(null);
  const [p2poolBusy, setP2poolBusy] = useState(false);
  const [p2poolError, setP2poolError] = useState<string | null>(null);
  const [mode, setMode] = useState<"main" | "mini" | "nano">("mini");
  const [walletId, setWalletId] = useState("");
  const [addPoolMessage, setAddPoolMessage] = useState<string | null>(null);

  function refreshAll() {
    api.monerodIntegrity().then(setMonerodIntegrity).catch(() => {});
    api.monerodStatus().then(setMonerodStatus).catch(() => {});
    api.p2poolIntegrity().then(setP2poolIntegrity).catch(() => {});
    api.p2poolStatus().then(setP2poolStatus).catch(() => {});
  }

  useEffect(() => {
    api.p2poolDefaults().then(setDefaults).catch(() => {});
    api.p2poolRequirements().then(setRequirements).catch(() => {});
    api.listWallets().then((w) => {
      setWallets(w);
      if (w.length > 0) setWalletId(String(w[0].id));
    }).catch(() => {});
    refreshAll();
    const interval = setInterval(refreshAll, POLL_MS);
    return () => clearInterval(interval);
  }, []);

  async function handleInstallMonerod() {
    setMonerodBusy(true);
    setMonerodError(null);
    try {
      await api.monerodInstall();
      refreshAll();
    } catch (e) {
      setMonerodError(e instanceof Error ? e.message : String(e));
    } finally {
      setMonerodBusy(false);
    }
  }

  async function handleStartMonerod() {
    if (!defaults) return;
    setMonerodBusy(true);
    setMonerodError(null);
    try {
      await api.monerodStart(defaults.monerod_data_dir, pruned, Number(bandwidthLimit) || null);
      setConfirmingSync(false);
      setUnderstandsSync(false);
      refreshAll();
    } catch (e) {
      setMonerodError(e instanceof Error ? e.message : String(e));
    } finally {
      setMonerodBusy(false);
    }
  }

  async function handleStopMonerod() {
    setMonerodBusy(true);
    try {
      await api.monerodStop();
      refreshAll();
    } finally {
      setMonerodBusy(false);
    }
  }

  async function handleInstallP2pool() {
    setP2poolBusy(true);
    setP2poolError(null);
    try {
      await api.p2poolInstall();
      refreshAll();
    } catch (e) {
      setP2poolError(e instanceof Error ? e.message : String(e));
    } finally {
      setP2poolBusy(false);
    }
  }

  async function handleStartP2pool() {
    if (!defaults || !walletId) return;
    setP2poolBusy(true);
    setP2poolError(null);
    try {
      await api.p2poolStart(Number(walletId), mode, defaults.p2pool_data_dir, defaults.p2pool_stratum_port, false);
      refreshAll();
    } catch (e) {
      setP2poolError(e instanceof Error ? e.message : String(e));
    } finally {
      setP2poolBusy(false);
    }
  }

  async function handleStopP2pool() {
    setP2poolBusy(true);
    try {
      await api.p2poolStop();
      refreshAll();
    } finally {
      setP2poolBusy(false);
    }
  }

  async function handleAddAsPool() {
    if (!defaults) return;
    setAddPoolMessage(null);
    try {
      await api.createPool({
        name: "P2Pool (local)",
        host: "127.0.0.1",
        port: defaults.p2pool_stratum_port,
        tls: false,
      });
      setAddPoolMessage("Added — go to Setup to see it, or select it on the dashboard's Real Mining panel.");
    } catch (e) {
      setAddPoolMessage(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">P2Pool</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">P2Pool — Decentralized Mining</h1>
          <p className="mt-1 text-sm text-zinc-500">
            P2Pool is a peer-to-peer mining pool: no central operator, 0% fee, trustless payouts
            straight to your wallet. The tradeoff is that it requires <em>your own</em> synced
            Monero node, which is a real, multi-day, tens-of-gigabytes commitment — read the
            requirements below before starting anything.
          </p>
        </div>

        {requirements && (
          <Card className="border-amber-500/30 bg-amber-500/5">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-amber-400">
                Before you start: what this actually costs
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm text-zinc-300">
              <p>
                <strong>Pruned node:</strong> ~{requirements.pruned_gb_low}–{requirements.pruned_gb_high} GB disk
              </p>
              <p>
                <strong>Full node:</strong> ~{requirements.full_gb_low}–{requirements.full_gb_high} GB disk
              </p>
              <p className="text-xs text-zinc-500">{requirements.note}</p>
              <p className="text-xs text-zinc-500">
                Sources:{" "}
                {requirements.sources.map((s, i) => (
                  <span key={s}>
                    {i > 0 && ", "}
                    <a href={s} target="_blank" rel="noreferrer" className="underline">
                      {new URL(s).hostname}
                    </a>
                  </span>
                ))}
              </p>
              <p>
                Sync also takes real time (hours to days depending on your connection) and real
                bandwidth — MacMine Lab lets you cap download speed below.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Monero node */}
        <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium text-zinc-400">Monero Node (monerod)</CardTitle>
            {monerodStatus && (
              <Badge variant="outline" className={monerodStatus.running ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}>
                {monerodStatus.running ? "Running" : "Stopped"}
              </Badge>
            )}
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {monerodIntegrity && !monerodIntegrity.installed && (
              <div className="flex items-center justify-between">
                <p className="text-xs text-zinc-500">
                  Not installed. Installs the official monerod binary via Homebrew (~94 MB, safe,
                  no blockchain download yet).
                </p>
                <Button size="sm" onClick={handleInstallMonerod} disabled={monerodBusy}>
                  {monerodBusy ? "Installing…" : "Install"}
                </Button>
              </div>
            )}
            {monerodIntegrity?.installed && (
              <p className="text-xs text-zinc-500">
                v{monerodIntegrity.version} ({monerodIntegrity.architecture}) via {monerodIntegrity.install_source}
              </p>
            )}

            {monerodStatus?.running ? (
              <>
                <div className="grid grid-cols-2 gap-3 font-mono text-xs sm:grid-cols-4">
                  <Metric label="Height" value={monerodStatus.height?.toLocaleString() ?? "starting…"} />
                  <Metric label="Target" value={monerodStatus.target_height?.toLocaleString() ?? "—"} />
                  <Metric label="Progress" value={monerodStatus.sync_progress_percent !== null ? `${monerodStatus.sync_progress_percent}%` : "—"} />
                  <Metric label="Synced" value={monerodStatus.synchronized === null ? "—" : monerodStatus.synchronized ? "yes" : "not yet"} />
                  <Metric label="DB size" value={monerodStatus.database_size_gb !== null ? `${monerodStatus.database_size_gb} GB` : "—"} />
                  <Metric label="Free space" value={monerodStatus.free_space_gb !== null ? `${monerodStatus.free_space_gb} GB` : "—"} />
                </div>
                <Button size="sm" variant="destructive" onClick={handleStopMonerod} disabled={monerodBusy} className="w-fit">
                  {monerodBusy ? "Stopping…" : "Stop Node"}
                </Button>
              </>
            ) : monerodIntegrity?.installed && !confirmingSync ? (
              <Button size="sm" onClick={() => setConfirmingSync(true)} className="w-fit">
                Start Node &amp; Begin Sync…
              </Button>
            ) : monerodIntegrity?.installed && confirmingSync ? (
              <div className="flex flex-col gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
                <p className="text-sm text-amber-300">
                  This will start downloading the Monero blockchain to{" "}
                  <code className="text-xs">{defaults?.monerod_data_dir}</code> — real disk space and
                  bandwidth, starting now.
                </p>
                <label className="flex items-center gap-2 text-sm text-zinc-300">
                  <Checkbox checked={pruned} onCheckedChange={(v) => setPruned(v === true)} />
                  Pruned mode (smaller, recommended)
                </label>
                <div className="flex items-center gap-2">
                  <Label className="text-xs text-zinc-500">Download limit (KB/s, 0 = unlimited)</Label>
                  <Input
                    value={bandwidthLimit}
                    onChange={(e) => setBandwidthLimit(e.target.value)}
                    className="w-24 font-mono"
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-zinc-300">
                  <Checkbox checked={understandsSync} onCheckedChange={(v) => setUnderstandsSync(v === true)} />
                  I understand this downloads tens of GB and may take hours to days
                </label>
                <div className="flex gap-2">
                  <Button size="sm" disabled={!understandsSync || monerodBusy} onClick={handleStartMonerod}>
                    {monerodBusy ? "Starting…" : "Confirm & Start Syncing"}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setConfirmingSync(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : null}
            {monerodError && <p className="text-xs text-red-400">{monerodError}</p>}
          </CardContent>
        </Card>

        {/* P2Pool */}
        <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium text-zinc-400">P2Pool</CardTitle>
            {p2poolStatus && (
              <Badge variant="outline" className={p2poolStatus.running ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}>
                {p2poolStatus.running ? "Running" : "Stopped"}
              </Badge>
            )}
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {p2poolIntegrity && !p2poolIntegrity.installed && (
              <div className="flex items-center justify-between">
                <p className="text-xs text-zinc-500">
                  Not installed. Downloads the official ~5 MB binary from GitHub and verifies its
                  SHA-256 against the project&apos;s signed checksums — small, safe to automate.
                </p>
                <Button size="sm" onClick={handleInstallP2pool} disabled={p2poolBusy}>
                  {p2poolBusy ? "Installing…" : "Install"}
                </Button>
              </div>
            )}
            {p2poolIntegrity?.installed && (
              <p className="text-xs text-zinc-500">
                {p2poolIntegrity.version} ({p2poolIntegrity.architecture}) — {p2poolIntegrity.verification_method}
              </p>
            )}

            {!p2poolStatus?.running && p2poolIntegrity?.installed && (
              <div className="flex flex-wrap items-end gap-3">
                <div className="flex flex-col gap-1.5">
                  <Label className="text-[10px] uppercase tracking-wider text-zinc-500">Wallet</Label>
                  <Select value={walletId} onValueChange={(v) => setWalletId(v ?? "")}>
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
                  <Label className="text-[10px] uppercase tracking-wider text-zinc-500">Sidechain</Label>
                  <Select value={mode} onValueChange={(v) => setMode((v as typeof mode) ?? "mini")}>
                    <SelectTrigger className="w-36">
                      <SelectValue>{(v: string) => v}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mini">mini (low hashrate)</SelectItem>
                      <SelectItem value="main">main</SelectItem>
                      <SelectItem value="nano">nano (lowest)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button size="sm" onClick={handleStartP2pool} disabled={p2poolBusy || wallets.length === 0}>
                  {p2poolBusy ? "Starting…" : "Start P2Pool"}
                </Button>
              </div>
            )}
            {wallets.length === 0 && (
              <p className="text-xs text-zinc-500">
                No wallet configured yet — <Link href="/setup" className="underline">add one in Setup</Link> first.
              </p>
            )}

            {p2poolStatus?.running && (
              <>
                <p className="text-xs text-zinc-500">
                  Local stratum server listening on 127.0.0.1:{p2poolStatus.stratum_port}. Note:
                  p2pool needs monerod fully synced to actually produce valid shares — check the
                  node status above.
                </p>
                <div className="flex gap-2">
                  <Button size="sm" variant="destructive" onClick={handleStopP2pool} disabled={p2poolBusy}>
                    {p2poolBusy ? "Stopping…" : "Stop P2Pool"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleAddAsPool}>
                    Add as Mining Pool
                  </Button>
                </div>
                {addPoolMessage && <p className="text-xs text-emerald-400">{addPoolMessage}</p>}
              </>
            )}
            {p2poolError && <p className="text-xs text-red-400">{p2poolError}</p>}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</span>
      <span className="text-zinc-200">{value}</span>
    </div>
  );
}
