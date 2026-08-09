import { Badge } from "@/components/ui/badge";
import type { ThermalInfo } from "@/lib/api";

const STYLES: Record<ThermalInfo["state"], string> = {
  NORMAL: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  WARM: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  HOT: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  CRITICAL: "bg-red-500/15 text-red-400 border-red-500/30",
  UNAVAILABLE: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

export function ThermalBadge({ thermal }: { thermal: ThermalInfo }) {
  return (
    <Badge variant="outline" className={STYLES[thermal.state]}>
      {thermal.state}
      {thermal.cpu_speed_limit_percent !== null && thermal.state !== "NORMAL"
        ? ` · ${thermal.cpu_speed_limit_percent}% speed`
        : ""}
    </Badge>
  );
}
