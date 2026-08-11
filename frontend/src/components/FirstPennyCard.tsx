"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type FirstPennyState } from "@/lib/api";

export function FirstPennyCard() {
  const [state, setState] = useState<FirstPennyState | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.firstPenny().then(setState).catch(() => setError(true));
  }, []);

  const target = state?.next_milestone_usd ?? 0.01;
  const progressPercent = state ? Math.min(state.progress_to_next_milestone * 100, 100) : 0;
  const unlockedCount = state?.achievements.filter((a) => a.unlocked).length ?? 0;

  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-zinc-400">First Penny Challenge</CardTitle>
        <Link href="/first-penny" className="text-xs text-zinc-500 hover:text-zinc-200">
          Details →
        </Link>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {error && <p className="text-xs text-zinc-500">Could not load progress right now.</p>}
        {state && (
          <>
            <div className="flex items-baseline justify-between font-mono">
              <span className="text-2xl tabular-nums">${state.estimated_usd_total.toFixed(4)}</span>
              <span className="text-sm text-zinc-500">/ ${target.toFixed(2)}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <p className="text-[11px] text-zinc-600">
              Estimated, not a real balance — {unlockedCount}/{state.achievements.length} achievements
              unlocked.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
