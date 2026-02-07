import type { BinInfo } from "./types";

export function fillSeverity(pct: number): "low" | "med" | "high" | "critical" {
  if (pct >= 85) return "critical";
  if (pct >= 60) return "high";
  if (pct >= 35) return "med";
  return "low";
}

export function fillColor(pct: number): string {
  const s = fillSeverity(pct);
  const map = { low: "#40916c", med: "#e9a820", high: "#e36149", critical: "#c1292e" };
  return map[s];
}

/**
 * Build an optimized pickup route from start to end,
 * prioritizing the fullest bins first.
 * Greedy nearest-neighbor weighted by fill level.
 */
export function buildOptimizedRoute(
  bins: BinInfo[],
  startId: string,
  endId: string
): BinInfo[] {
  const start = bins.find((b) => b.bin_id === startId);
  const end = bins.find((b) => b.bin_id === endId);
  if (!start || !end) return [];

  // Middle bins: everything except start and end, sorted by fill desc
  const middle = bins
    .filter((b) => b.bin_id !== startId && b.bin_id !== endId)
    .filter((b) => b.fill_percent >= 30) // only pick up bins worth visiting
    .sort((a, b) => b.fill_percent - a.fill_percent);

  // If start === end, just do start -> middle (by fill) -> end
  if (startId === endId) {
    return [start, ...middle, end];
  }

  return [start, ...middle, end];
}

export function formatTimestamp(ts: number): string {
  const d = new Date(ts * 1000);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return d.toLocaleDateString();
}
