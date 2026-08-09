"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type AnalyticsResponse, type AnalyticsSeries } from "@/lib/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);

  useEffect(() => {
    api.analytics().then(setData).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">Analytics</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">Analytics</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Real relationships from your own measured data only — a chart says &quot;not enough
            data yet&quot; rather than drawing a line through one or two points.
          </p>
        </div>

        {data && (
          <div className="grid gap-6 sm:grid-cols-2">
            <ScatterCard
              title="Threads vs. Hashrate"
              series={data.threads_vs_hashrate}
              xLabel="threads"
              yLabel="H/s"
            />
            <ScatterCard
              title="Threads vs. Efficiency"
              series={data.threads_vs_efficiency}
              xLabel="threads"
              yLabel="H/s per thread"
            />
            <ScatterCard
              title="Mining Session Length vs. Hashrate"
              series={data.session_duration_vs_hashrate}
              xLabel="duration (s)"
              yLabel="H/s"
            />
            <BarCard title="Thermal State vs. Avg Hashrate" series={data.thermal_state_vs_hashrate} />
          </div>
        )}
      </main>
    </div>
  );
}

function ScatterCard({
  title,
  series,
  xLabel,
  yLabel,
}: {
  title: string;
  series: AnalyticsSeries;
  xLabel: string;
  yLabel: string;
}) {
  return (
    <Card className="border-white/10 bg-zinc-900/60">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {!series.available ? (
          <p className="flex h-48 items-center justify-center text-center text-xs text-zinc-600">
            {series.reason}
          </p>
        ) : (
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="x"
                  type="number"
                  name={xLabel}
                  stroke="#52525b"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis dataKey="y" type="number" name={yLabel} stroke="#52525b" fontSize={11} tickLine={false} />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{
                    background: "#18181b",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Scatter data={series.points} fill="#34d399" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BarCard({ title, series }: { title: string; series: AnalyticsSeries }) {
  return (
    <Card className="border-white/10 bg-zinc-900/60">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {!series.available ? (
          <p className="flex h-48 items-center justify-center text-center text-xs text-zinc-600">
            {series.reason}
          </p>
        ) : (
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series.points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="x" stroke="#52525b" fontSize={11} tickLine={false} />
                <YAxis stroke="#52525b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "#18181b",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="y" fill="#34d399" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
