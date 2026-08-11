"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { SeedPhraseWarning } from "@/components/SeedPhraseWarning";
import { WalletSection } from "@/components/WalletSection";
import { PoolSection } from "@/components/PoolSection";
import { SafetySettingsSection } from "@/components/SafetySettingsSection";
import { api, type Pool, type Wallet } from "@/lib/api";

export default function SetupPage() {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [pools, setPools] = useState<Pool[]>([]);

  const refresh = useCallback(() => {
    api.listWallets().then(setWallets).catch(() => {});
    api.listPools().then(setPools).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const ready = wallets.length > 0 && pools.length > 0;

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">Setup</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">Set up real mining</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Real mining sends actual RandomX work to a pool of your choosing and pays out to a
            wallet address you control. MacMine Lab needs two things from you: a public address to
            receive rewards, and a pool to mine at.
          </p>
        </div>

        <SeedPhraseWarning />

        <WalletSection wallets={wallets} onChanged={refresh} />
        <PoolSection pools={pools} onChanged={refresh} />
        <SafetySettingsSection />

        <div className="rounded-lg border border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30 p-4 text-sm">
          {ready ? (
            <p className="text-emerald-400">
              Wallet and pool configured — head to the{" "}
              <Link href="/" className="underline">
                dashboard
              </Link>{" "}
              to start mining.
            </p>
          ) : (
            <p className="text-zinc-500">
              {wallets.length === 0 && pools.length === 0
                ? "Add a wallet address and a pool above to enable real mining."
                : wallets.length === 0
                  ? "Add a wallet address above to enable real mining."
                  : "Add a pool above to enable real mining."}
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
