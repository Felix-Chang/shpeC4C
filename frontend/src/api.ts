import type { BinInfo } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchBins(): Promise<BinInfo[]> {
  const res = await fetch(`${API_BASE}/bins`);
  if (!res.ok) throw new Error(`Failed to fetch bins: ${res.status}`);
  return res.json();
}
