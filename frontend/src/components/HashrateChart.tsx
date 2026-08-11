"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface ChartPoint {
  t: number; // seconds since chart start
  hs: number;
}

export function HashrateChart({ points }: { points: ChartPoint[] }) {
  if (points.length < 2) {
    return (
      <div className="flex h-32 flex-col items-center justify-center gap-3 text-center">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-zinc-700">
          <path
            d="M3 17 8 11l4 3 5-7 4 4"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <p className="max-w-xs text-sm text-zinc-500">
          {points.length === 0
            ? "No live hashrate data yet — start a benchmark to see this fill in."
            : "Collecting samples…"}
        </p>
      </div>
    );
  }

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
          <XAxis
            dataKey="t"
            tickFormatter={(v: number) => `${v}s`}
            stroke="#52525b"
            fontSize={11}
            tickLine={false}
          />
          <YAxis
            width={64}
            stroke="#52525b"
            fontSize={11}
            tickLine={false}
            tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${v}`)}
          />
          <Tooltip
            contentStyle={{
              background: "#18181b",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(v) => `${v}s`}
            formatter={(v) => [`${Number(v).toFixed(1)} H/s`, "hashrate"]}
          />
          <Line
            type="monotone"
            dataKey="hs"
            stroke="#34d399"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
