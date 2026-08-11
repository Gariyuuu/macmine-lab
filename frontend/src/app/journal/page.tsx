"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type CalibrationRecommendation, type JournalResponse } from "@/lib/api";
import { formatHashrate, formatTimeAgo } from "@/lib/format";

export default function JournalPage() {
  const [data, setData] = useState<JournalResponse | null>(null);

  useEffect(() => {
    api.journal(200).then(setData).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">Experiment Journal</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">Experiment Journal</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Every benchmark you&apos;ve run, with recommended Eco/Balanced/Performance thread
            counts computed from your own measured results — not assumed.
          </p>
        </div>

        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              <RecCard label="Best Eco Config" rec={data.recommendations.eco} />
              <RecCard label="Best Balanced Config" rec={data.recommendations.balanced} />
              <RecCard label="Best Performance Config" rec={data.recommendations.performance} />
            </div>

            <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-zinc-400">
                  All Experiments ({data.runs.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.runs.length === 0 ? (
                  <p className="text-sm text-zinc-500">
                    No benchmarks run yet — run one from the dashboard to start the journal.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[640px] font-mono text-xs">
                      <thead className="text-zinc-500">
                        <tr className="text-left">
                          <th className="pb-2 pr-4 font-normal">When</th>
                          <th className="pb-2 pr-4 font-normal">Threads</th>
                          <th className="pb-2 pr-4 font-normal">Avg H/s</th>
                          <th className="pb-2 pr-4 font-normal">H/s per thread</th>
                          <th className="pb-2 pr-4 font-normal">Thermal</th>
                          <th className="pb-2 font-normal">Result</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.runs.map((r) => (
                          <tr key={r.id} className="border-t border-white/5 text-zinc-300">
                            <td className="py-2 pr-4 text-zinc-500">{formatTimeAgo(r.started_at)}</td>
                            <td className="py-2 pr-4">{r.threads}</td>
                            <td className="py-2 pr-4">{formatHashrate(r.avg_hs)}</td>
                            <td className="py-2 pr-4">{formatHashrate(r.hs_per_thread)}</td>
                            <td className="py-2 pr-4">{r.final_thermal_state}</td>
                            <td className="py-2 text-zinc-400">{r.result_label}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

function RecCard({ label, rec }: { label: string; rec: CalibrationRecommendation }) {
  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardContent className="flex flex-col gap-1 py-4">
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</span>
        {rec.tested ? (
          <>
            <span className="font-mono text-xl">{rec.threads} threads</span>
            <span className="text-xs text-zinc-500">{formatHashrate(rec.avg_hs)}</span>
          </>
        ) : (
          <span className="text-sm text-zinc-600">Not enough data yet</span>
        )}
      </CardContent>
    </Card>
  );
}
