import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThermalBadge } from "./ThermalBadge";
import { formatGb, formatPercent } from "@/lib/format";
import type { MinerStatus, SystemTelemetry } from "@/lib/api";

export function SystemHealthPanel({
  telemetry,
  miner,
}: {
  telemetry: SystemTelemetry | null;
  miner: MinerStatus | null;
}) {
  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-400">System Health</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-y-4 gap-x-6 font-mono text-sm sm:grid-cols-3">
        <Metric label="CPU usage" value={formatPercent(telemetry?.cpu.user_percent)} />
        <Metric
          label="Miner CPU"
          value={miner?.running ? formatPercent(miner.cpu_percent) : "not running"}
        />
        <Metric
          label="Load avg (1m)"
          value={telemetry?.cpu.load_avg_1m?.toFixed(2) ?? "Unavailable"}
        />
        <Metric label="Memory used" value={formatGb(telemetry?.memory.used_gb)} />
        <Metric label="Memory free" value={formatGb(telemetry?.memory.unused_gb)} />
        <Metric
          label="Battery"
          value={
            telemetry?.battery.percent !== null && telemetry?.battery.percent !== undefined
              ? `${telemetry.battery.percent}% (${telemetry.battery.raw_status ?? "?"})`
              : "Unavailable"
          }
        />
        <Metric
          label="Power source"
          value={
            telemetry?.battery.on_ac_power === null || telemetry?.battery.on_ac_power === undefined
              ? "Unavailable"
              : telemetry.battery.on_ac_power
                ? "AC Power"
                : "Battery"
          }
        />
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-zinc-500">Thermal state</span>
          {telemetry ? (
            <ThermalBadge thermal={telemetry.thermal} />
          ) : (
            <span className="text-zinc-500">Unavailable</span>
          )}
        </div>
      </CardContent>
    </Card>
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
