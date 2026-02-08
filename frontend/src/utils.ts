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
