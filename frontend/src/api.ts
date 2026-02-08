import type { BinInfo, RouteOut } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchBins(): Promise<BinInfo[]> {
  const res = await fetch(`${API_BASE}/bins`);
  if (!res.ok) throw new Error(`Failed to fetch bins: ${res.status}`);
  return res.json();
}

export async function fetchRoute(
  startId: string,
  endId: string
): Promise<RouteOut> {
  const res = await fetch(`${API_BASE}/route?start=${startId}&end=${endId}`);
  if (!res.ok) {
    throw new Error(`Route fetch failed: ${res.statusText}`);
  }
  return res.json();
}
