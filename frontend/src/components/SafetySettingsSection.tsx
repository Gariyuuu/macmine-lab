"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { api, type SafetySettings } from "@/lib/api";

export function SafetySettingsSection() {
  const [settings, setSettings] = useState<SafetySettings | null>(null);
  const [threshold, setThreshold] = useState("30");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.safetySettings().then((s) => {
      setSettings(s);
      setThreshold(String(s.battery_pause_threshold_percent));
    }).catch(() => {});
  }, []);

  async function update(partial: {
    safety_automation_enabled?: boolean;
    allow_mining_on_battery?: boolean;
    battery_pause_threshold_percent?: number;
  }) {
    setSaving(true);
    setSaved(false);
    try {
      const result = await api.setSafetySettings(partial);
      setSettings(result);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return (
      <Card className="border-white/10 bg-zinc-900/60">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-400">Safety</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-zinc-500">Loading…</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/10 bg-zinc-900/60">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">Safety</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-xs text-zinc-500">
          Critical thermal state always stops mining immediately — that can&apos;t be turned off.
          Everything below is optional automation on top of that hard floor.
        </p>

        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <Checkbox
            checked={settings.automation_enabled}
            onCheckedChange={(v) => update({ safety_automation_enabled: v === true })}
          />
          Automatically notify on warm/hot temperatures and reduce mining threads when hot
        </label>

        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <Checkbox
            checked={settings.allow_mining_on_battery}
            onCheckedChange={(v) => update({ allow_mining_on_battery: v === true })}
          />
          Allow mining on battery power (default: pause when unplugged)
        </label>

        <div className="flex items-end gap-3">
          <div className="flex flex-col gap-1.5">
            <Label className="text-[10px] uppercase tracking-wider text-zinc-500">
              Pause mining below battery %
            </Label>
            <Input
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              className="w-24 font-mono"
              inputMode="numeric"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={saving}
            onClick={() => update({ battery_pause_threshold_percent: Number(threshold) })}
          >
            {saving ? "Saving…" : "Save"}
          </Button>
          {saved && <span className="text-xs text-emerald-400">Saved.</span>}
        </div>
      </CardContent>
    </Card>
  );
}
