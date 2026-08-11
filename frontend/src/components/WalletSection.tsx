"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { api, type AddressValidation, type Wallet } from "@/lib/api";

export function WalletSection({
  wallets,
  onChanged,
}: {
  wallets: Wallet[];
  onChanged: () => void;
}) {
  const [address, setAddress] = useState("");
  const [label, setLabel] = useState("");
  const [validation, setValidation] = useState<AddressValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addressEntered = address.trim() !== "";

  // Only the debounced fetch's own callbacks touch state here — nothing is
  // set synchronously in the effect body itself (avoids cascading renders).
  useEffect(() => {
    if (!addressEntered) return;
    const handle = setTimeout(() => {
      setValidating(true);
      api
        .validateWallet(address)
        .then(setValidation)
        .catch(() => setValidation(null))
        .finally(() => setValidating(false));
    }, 300);
    return () => clearTimeout(handle);
  }, [address, addressEntered]);

  async function handleSave() {
    setError(null);
    setSaving(true);
    try {
      await api.createWallet(address, label || undefined);
      setAddress("");
      setLabel("");
      setValidation(null);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    await api.deleteWallet(id);
    onChanged();
  }

  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">Wallet — Public Address</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-xs text-zinc-500">
          Enter the public Monero (XMR) address that should receive mining rewards. Get one from
          any legitimate Monero wallet — the official{" "}
          <a
            href="https://www.getmonero.org/downloads/"
            target="_blank"
            rel="noreferrer"
            className="underline hover:text-zinc-300"
          >
            Monero CLI/GUI wallet
          </a>{" "}
          or a reputable wallet app of your choice.
        </p>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="wallet-address" className="text-[10px] uppercase tracking-wider text-zinc-500">
            XMR Address
          </Label>
          <Input
            id="wallet-address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="YOUR_XMR_WALLET_ADDRESS"
            className="font-mono text-xs"
            spellCheck={false}
            autoComplete="off"
          />
          {addressEntered && validating && <span className="text-xs text-zinc-500">Checking format…</span>}
          {addressEntered && !validating && validation && (
            <span className={`text-xs ${validation.valid ? "text-emerald-400" : "text-red-400"}`}>
              {validation.valid
                ? `Looks like a valid ${validation.kind} address (format only — not a full checksum check).`
                : validation.reason}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="wallet-label" className="text-[10px] uppercase tracking-wider text-zinc-500">
            Label (optional)
          </Label>
          <Input
            id="wallet-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. Main wallet"
            className="max-w-xs"
          />
        </div>

        <Button
          onClick={handleSave}
          disabled={!addressEntered || !validation?.valid || saving}
          className="w-fit"
        >
          {saving ? "Saving…" : "Save Wallet"}
        </Button>
        {error && <p className="text-xs text-red-400">{error}</p>}

        {wallets.length > 0 && (
          <div className="mt-2 flex flex-col gap-2 border-t border-white/5 pt-4">
            {wallets.map((w) => (
              <div key={w.id} className="flex items-center justify-between gap-3 text-xs">
                <div className="flex min-w-0 items-center gap-2">
                  <Badge variant="outline" className="border-zinc-700 text-zinc-400">
                    {w.address_kind}
                  </Badge>
                  <span className="truncate font-mono text-zinc-300">{w.address}</span>
                  {w.label && <span className="shrink-0 text-zinc-500">({w.label})</span>}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="shrink-0 text-zinc-500 hover:text-red-400"
                  onClick={() => handleDelete(w.id)}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
