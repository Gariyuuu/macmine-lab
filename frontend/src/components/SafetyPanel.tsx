import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThermalBadge } from "./ThermalBadge";
import type { SafetyStatus, SystemTelemetry } from "@/lib/api";
import { formatTimeAgo } from "@/lib/format";

const ACTION_LABELS: Record<string, string> = {
  thermal_critical_stop: "Stopped mining — critical thermal state",
  thermal_warm_notify: "Notified — Mac warming up",
  battery_ac_disconnected_stop: "Stopped mining — power adapter disconnected",
  battery_low_stop: "Stopped mining — battery below threshold",
};

function describeAction(action: string | null): string | null {
  if (!action) return null;
  if (action in ACTION_LABELS) return ACTION_LABELS[action];
  if (action.startsWith("thermal_hot_reduced_to_")) {
    const threads = action.replace("thermal_hot_reduced_to_", "").replace("_threads", "");
    return `Reduced mining to ${threads} threads — running hot`;
  }
  return action;
}

export function SafetyPanel({
  telemetry,
  safety,
}: {
  telemetry: SystemTelemetry | null;
  safety: SafetyStatus | null;
}) {
  const actionDescription = describeAction(safety?.last_action ?? null);

  return (
    <Card className="border-white/10 bg-zinc-900/60">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-zinc-400">Safety</CardTitle>
        <span className={`flex items-center gap-1.5 text-xs ${safety?.watching ? "text-emerald-400" : "text-zinc-600"}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${safety?.watching ? "bg-emerald-400" : "bg-zinc-700"}`} />
          {safety?.watching ? "Watching" : "Not watching"}
        </span>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-400">
          {telemetry && <ThermalBadge thermal={telemetry.thermal} />}
          <span>
            {safety?.automation_enabled ? "Automation ON" : "Automation OFF (manual control)"}
          </span>
          <span>
            {safety?.allow_mining_on_battery
              ? `Mining on battery allowed (pauses below ${safety.battery_pause_threshold_percent}%)`
              : "Mining pauses if unplugged"}
          </span>
        </div>
        {actionDescription && (
          <p className="text-xs text-amber-400">
            Last action: {actionDescription}
            {safety?.last_action_at && ` · ${formatTimeAgo(safety.last_action_at)}`}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
