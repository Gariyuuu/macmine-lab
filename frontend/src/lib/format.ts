export function formatHashrate(hs: number | null | undefined): string {
  if (hs === null || hs === undefined) return "—";
  if (hs >= 1000) return `${(hs / 1000).toFixed(2)} kH/s`;
  return `${hs.toFixed(1)} H/s`;
}

export function formatPercent(v: number | null | undefined, digits = 0): string {
  if (v === null || v === undefined) return "Unavailable";
  return `${v.toFixed(digits)}%`;
}

export function formatGb(v: number | null | undefined): string {
  if (v === null || v === undefined) return "Unavailable";
  return `${v.toFixed(1)} GB`;
}

export function formatTimeAgo(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(isoString).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}
