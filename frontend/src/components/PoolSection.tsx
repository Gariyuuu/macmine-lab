"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { api, type Pool, type PoolConnectionTestResult } from "@/lib/api";

export function PoolSection({ pools, onChanged }: { pools: Pool[]; onChanged: () => void }) {
  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("3333");
  const [tls, setTls] = useState(false);
  const [workerName, setWorkerName] = useState("");
  const [testResult, setTestResult] = useState<PoolConnectionTestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const portNum = Number(port);
  const formValid = name.trim() !== "" && host.trim() !== "" && Number.isInteger(portNum) && portNum > 0;

  async function handleTest() {
    setTestResult(null);
    setTesting(true);
    try {
      const result = await api.testPoolConnection(host, portNum, tls);
      setTestResult(result);
    } catch (e) {
      setTestResult({ success: false, latency_ms: null, message: e instanceof Error ? e.message : String(e) });
    } finally {
      setTesting(false);
    }
  }

  async function handleSave() {
    setError(null);
    setSaving(true);
    try {
      await api.createPool({
        name,
        host,
        port: portNum,
        tls,
        worker_name: workerName || null,
      });
      setName("");
      setHost("");
      setPort("3333");
      setTls(false);
      setWorkerName("");
      setTestResult(null);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    await api.deletePool(id);
    onChanged();
  }

  return (
    <Card className="border-white/10 bg-zinc-900/60">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">Mining Pool</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-xs text-zinc-500">
          Add a traditional pool&apos;s connection details yourself — MacMine Lab does not ship
          any pool preset, since pool connection details change and we don&apos;t want to point
          your hashpower at something stale or wrong. Check the pool&apos;s own official site for
          its current host, port, and fee before adding it here.
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Pool Name">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My Pool" />
          </Field>
          <Field label="Worker Name (optional)">
            <Input value={workerName} onChange={(e) => setWorkerName(e.target.value)} placeholder="macmine" />
          </Field>
          <Field label="Host">
            <Input
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="pool.example.com"
              className="font-mono"
              spellCheck={false}
            />
          </Field>
          <Field label="Port">
            <Input
              value={port}
              onChange={(e) => setPort(e.target.value)}
              inputMode="numeric"
              className="font-mono"
            />
          </Field>
        </div>

        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <Checkbox checked={tls} onCheckedChange={(v) => setTls(v === true)} />
          Use TLS/SSL
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <Button variant="outline" onClick={handleTest} disabled={!formValid || testing}>
            {testing ? "Testing…" : "Test Connection"}
          </Button>
          <Button onClick={handleSave} disabled={!formValid || saving}>
            {saving ? "Saving…" : "Save Pool"}
          </Button>
        </div>

        {testResult && (
          <p className={`text-xs ${testResult.success ? "text-emerald-400" : "text-red-400"}`}>
            {testResult.message}
            {testResult.latency_ms !== null && ` (${testResult.latency_ms}ms)`}
            {" — "}
            <span className="text-zinc-500">
              network reachability only; the mining protocol itself is only tested once you start
              mining.
            </span>
          </p>
        )}
        {error && <p className="text-xs text-red-400">{error}</p>}

        {pools.length > 0 && (
          <div className="mt-2 flex flex-col gap-2 border-t border-white/5 pt-4">
            {pools.map((p) => (
              <div key={p.id} className="flex items-center justify-between gap-3 text-xs">
                <div className="flex min-w-0 items-center gap-2 font-mono text-zinc-300">
                  <span className="font-sans text-zinc-200">{p.name}</span>
                  <span className="text-zinc-500">
                    {p.host}:{p.port}
                    {p.tls ? " (TLS)" : ""}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="shrink-0 text-zinc-500 hover:text-red-400"
                  onClick={() => handleDelete(p.id)}
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</Label>
      {children}
    </div>
  );
}
