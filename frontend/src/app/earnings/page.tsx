"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  api,
  type EarningsEstimate,
  type NetworkSnapshot,
  type PriceSnapshot,
} from "@/lib/api";
import { formatHashrate, formatTimeAgo } from "@/lib/format";

export default function EarningsPage() {
  const [price, setPrice] = useState<PriceSnapshot | null>(null);
  const [priceError, setPriceError] = useState<string | null>(null);
  const [network, setNetwork] = useState<NetworkSnapshot | null>(null);
  const [networkError, setNetworkError] = useState<string | null>(null);

  const [hashrate, setHashrate] = useState("1000");
  const [electricityRate, setElectricityRate] = useState("0.15");
  const [powerDraw, setPowerDraw] = useState("30");
  const [estimate, setEstimate] = useState<EarningsEstimate | null>(null);
  const [estimateError, setEstimateError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.price().then(setPrice).catch((e) => setPriceError(e instanceof Error ? e.message : String(e)));
    api.network().then(setNetwork).catch((e) => setNetworkError(e instanceof Error ? e.message : String(e)));
    api.economicsSettings().then((s) => {
      if (s.electricity_rate_usd_per_kwh !== null) setElectricityRate(String(s.electricity_rate_usd_per_kwh));
      if (s.power_draw_watts !== null) setPowerDraw(String(s.power_draw_watts));
    }).catch(() => {});

    // Suggest a starting hashrate from the most recent real measurement, if any.
    api.benchmarkHistory(1).then((runs) => {
      if (runs[0]?.avg_hs) setHashrate(String(Math.round(runs[0].avg_hs)));
    }).catch(() => {});
    api.miningHistory(1).then((sessions) => {
      if (sessions[0]?.avg_hs) setHashrate(String(Math.round(sessions[0].avg_hs)));
    }).catch(() => {});
  }, []);

  async function handleCalculate() {
    setEstimateError(null);
    setSaving(true);
    try {
      await api.setEconomicsSettings({
        electricity_rate_usd_per_kwh: Number(electricityRate) || null,
        power_draw_watts: Number(powerDraw) || null,
      });
      const result = await api.estimateEarnings(Number(hashrate));
      setEstimate(result);
    } catch (e) {
      setEstimateError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">Earnings</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">Earnings Estimate</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Every number below is an <strong className="text-zinc-300">estimate</strong> calculated
            from your hashrate, current network difficulty, and current XMR price — not a pool
            balance or a wallet balance. If price or network data can&apos;t be fetched, this page
            says so instead of guessing.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Card className="border-white/10 bg-zinc-900/60">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400">XMR Price</CardTitle>
            </CardHeader>
            <CardContent>
              {price ? (
                <>
                  <div className="font-mono text-2xl">${price.price_usd.toFixed(2)}</div>
                  <div className="mt-1 text-xs text-zinc-500">
                    {price.source} · updated {formatTimeAgo(price.fetched_at)}
                  </div>
                </>
              ) : (
                <div className="text-sm text-red-400">
                  {priceError ? "PRICE DATA UNAVAILABLE" : "Loading…"}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-zinc-900/60">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400">Network</CardTitle>
            </CardHeader>
            <CardContent>
              {network ? (
                <>
                  <div className="font-mono text-sm">
                    {formatHashrate(network.network_hash_rate)} network hashrate
                  </div>
                  <div className="font-mono text-sm text-zinc-400">
                    {network.block_reward_xmr.toFixed(4)} XMR/block · {network.block_time_s}s target
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    {network.source} · height {network.height} · updated {formatTimeAgo(network.fetched_at)}
                  </div>
                </>
              ) : (
                <div className="text-sm text-red-400">
                  {networkError ? "NETWORK DATA UNAVAILABLE" : "Loading…"}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="border-white/10 bg-zinc-900/60">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zinc-400">Your inputs</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <Label className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Your hashrate (H/s)
                </Label>
                <Input value={hashrate} onChange={(e) => setHashrate(e.target.value)} className="font-mono" />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Electricity ($/kWh)
                </Label>
                <Input
                  value={electricityRate}
                  onChange={(e) => setElectricityRate(e.target.value)}
                  className="font-mono"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Power draw (W, your estimate)
                </Label>
                <Input value={powerDraw} onChange={(e) => setPowerDraw(e.target.value)} className="font-mono" />
              </div>
            </div>
            <p className="text-xs text-zinc-500">
              Power draw isn&apos;t measured — macOS doesn&apos;t expose real-time power draw without
              elevated permissions, which MacMine Lab avoids. Enter your own estimate (check About
              This Mac / a wall meter, or your Mac&apos;s published TDP as a rough guide).
            </p>
            <Button onClick={handleCalculate} disabled={saving} className="w-fit">
              {saving ? "Calculating…" : "Calculate"}
            </Button>
            {estimateError && <p className="text-xs text-red-400">{estimateError}</p>}
          </CardContent>
        </Card>

        {estimate && (
          <Card className="border-white/10 bg-zinc-900/60">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400">Estimate</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-y-4 gap-x-6 font-mono text-sm sm:grid-cols-3">
              <Metric label="XMR / hour" value={estimate.xmr_per_hour.toFixed(6)} />
              <Metric label="XMR / day" value={estimate.xmr_per_day.toFixed(6)} />
              <Metric label="Your share of network" value={`${(estimate.my_share_of_network * 100).toExponential(2)}%`} />
              <Metric label="USD / hour" value={`$${estimate.usd_per_hour.toFixed(4)}`} />
              <Metric label="USD / day" value={`$${estimate.usd_per_day.toFixed(4)}`} />
              {estimate.electricity_cost_per_day_usd !== null && (
                <Metric label="Electricity / day" value={`$${estimate.electricity_cost_per_day_usd.toFixed(4)}`} />
              )}
              {estimate.net_usd_per_day !== null && (
                <Metric
                  label="Net / day"
                  value={`${estimate.net_usd_per_day >= 0 ? "" : "-"}$${Math.abs(estimate.net_usd_per_day).toFixed(4)}`}
                />
              )}
            </CardContent>
          </Card>
        )}
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
