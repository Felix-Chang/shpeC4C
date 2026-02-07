import { useState, useEffect, useCallback, useMemo } from "react";
import { APIProvider, Map as GoogleMap } from "@vis.gl/react-google-maps";
import "./App.css";
import { fetchBins } from "./api";
import type { BinInfo } from "./types";
import {
  fillSeverity,
  fillColor,
  buildOptimizedRoute,
  formatTimestamp,
} from "./utils";
import BinMarker from "./BinMarker";

const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY || "";
const POLL_INTERVAL = 10_000;
const DEFAULT_CENTER = { lat: 29.6462, lng: -82.3479 };

function App() {
  const [bins, setBins] = useState<BinInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBin, setSelectedBin] = useState<string | null>(null);
  const [startBin, setStartBin] = useState("");
  const [endBin, setEndBin] = useState("");
  const [route, setRoute] = useState<BinInfo[] | null>(null);
  const [activeNav, setActiveNav] = useState<"bins" | "route">("bins");

  const loadBins = useCallback(async () => {
    try {
      const data = await fetchBins();
      setBins(data);
    } catch (err) {
      console.error("Failed to load bins:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBins();
    const interval = setInterval(loadBins, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [loadBins]);

  const stats = useMemo(() => {
    if (!bins.length) return { total: 0, critical: 0, avgFill: 0 };
    const critical = bins.filter((b) => b.fill_percent >= 85).length;
    const avgFill = bins.reduce((s, b) => s + b.fill_percent, 0) / bins.length;
    return { total: bins.length, critical, avgFill: Math.round(avgFill) };
  }, [bins]);

  const mapCenter = useMemo(() => {
    const valid = bins.filter((b) => b.lat !== 0 || b.lng !== 0);
    if (!valid.length) return DEFAULT_CENTER;
    const lat = valid.reduce((s, b) => s + b.lat, 0) / valid.length;
    const lng = valid.reduce((s, b) => s + b.lng, 0) / valid.length;
    return { lat, lng };
  }, [bins]);

  const routeOrderMap = useMemo(() => {
    const m = new Map<string, number>();
    if (route) {
      route.forEach((b, i) => m.set(b.bin_id, i + 1));
    }
    return m;
  }, [route]);

  const handleBuildRoute = () => {
    if (!startBin || !endBin) return;
    const optimized = buildOptimizedRoute(bins, startBin, endBin);
    setRoute(optimized);
  };

  const handleClearRoute = () => {
    setRoute(null);
    setStartBin("");
    setEndBin("");
  };

  const sortedBins = useMemo(
    () => [...bins].sort((a, b) => b.fill_percent - a.fill_percent),
    [bins],
  );

  const selected = bins.find((b) => b.bin_id === selectedBin);

  if (loading) {
    return <div className="loading">Loading bins...</div>;
  }

  return (
    <div className="app">
      {/* ---- Icon Rail ---- */}
      <nav className="icon-rail">
        <div className="rail-top">
          <div className="rail-logo">
            <svg width="26" height="26" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="8" fill="#2d6a4f" />
              <path d="M8 10h12l-1.5 11a1 1 0 01-1 .9h-7a1 1 0 01-1-.9L8 10z" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M7 10h14" stroke="white" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M11 7h6" stroke="white" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </div>

          <button
            className={`rail-btn ${activeNav === "bins" ? "active" : ""}`}
            onClick={() => setActiveNav("bins")}
            title="Analytics"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </button>

          <button
            className={`rail-btn ${activeNav === "route" ? "active" : ""}`}
            onClick={() => setActiveNav("route")}
            title="Route Planner"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
            </svg>
          </button>
        </div>
      </nav>

      {/* ---- Content Panel ---- */}
      <div className="panel">
        <div className="panel-header">
          <h1 className="panel-title">BinSight</h1>
          <p className="panel-subtitle">Smart Collection Dashboard</p>
        </div>

        {/* Stats pills */}
        <div className="stats-row">
          <div className="stat-pill">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">bins</span>
          </div>
          <div className="stat-pill">
            <span className={`stat-value ${stats.critical > 0 ? "critical" : "good"}`}>
              {stats.critical}
            </span>
            <span className="stat-label">critical</span>
          </div>
          <div className="stat-pill">
            <span className={`stat-value ${stats.avgFill >= 70 ? "critical" : stats.avgFill >= 40 ? "warning" : "good"}`}>
              {stats.avgFill}%
            </span>
            <span className="stat-label">avg fill</span>
          </div>
        </div>

        {/* Route Planner — shown when route nav is active */}
        {activeNav === "route" && (
          <div className="route-planner fade-in">
            <div className="route-planner-title">Route Planner</div>
            <div className="route-endpoints">
              <div className="route-endpoint">
                <div className="endpoint-dot start" />
                <div className="endpoint-field">
                  <label>Start</label>
                  <select value={startBin} onChange={(e) => setStartBin(e.target.value)}>
                    <option value="">Select bin...</option>
                    {bins.map((b) => (
                      <option key={b.bin_id} value={b.bin_id}>
                        {b.name} ({Math.round(b.fill_percent)}%)
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="endpoint-line" />
              <div className="route-endpoint">
                <div className="endpoint-dot end" />
                <div className="endpoint-field">
                  <label>End</label>
                  <select value={endBin} onChange={(e) => setEndBin(e.target.value)}>
                    <option value="">Select bin...</option>
                    {bins.map((b) => (
                      <option key={b.bin_id} value={b.bin_id}>
                        {b.name} ({Math.round(b.fill_percent)}%)
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div className="route-actions">
              <button className="btn-route primary" onClick={handleBuildRoute} disabled={!startBin || !endBin}>
                Optimize Route
              </button>
              {route && (
                <button className="btn-route secondary" onClick={handleClearRoute}>Clear</button>
              )}
            </div>
            {route && (
              <div className="route-info fade-in">
                <div className="route-info-header">
                  <strong>{route.length} stops</strong>
                  <span>Fullest bins first</span>
                </div>
                <ul className="route-stop-list">
                  {route.map((b, i) => (
                    <li key={b.bin_id}>
                      <span className="route-stop-number">{i + 1}</span>
                      <span className="route-stop-name">{b.name}</span>
                      <span className="route-stop-fill" style={{ color: fillColor(b.fill_percent) }}>
                        {Math.round(b.fill_percent)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Bin Cards */}
        <div className="panel-section-title">
          {activeNav === "route" && route ? "Route Bins" : "Active Bins"}
        </div>

        <div className="bin-list">
          {sortedBins.map((bin, i) => {
            const severity = fillSeverity(bin.fill_percent);
            const isRouteStop = routeOrderMap.has(bin.bin_id);
            const routeNum = routeOrderMap.get(bin.bin_id);
            const isSelected = selectedBin === bin.bin_id;

            return (
              <div
                key={bin.bin_id}
                className={`bin-card ${isSelected ? "selected" : ""} ${isRouteStop ? "route-stop" : ""}`}
                style={{ animationDelay: `${i * 50}ms` }}
                onClick={() => setSelectedBin(isSelected ? null : bin.bin_id)}
              >
                <div className={`bin-card-edge ${severity}`} />
                <div className="bin-card-body">
                  <div className="bin-card-top">
                    <div className="bin-card-name-row">
                      {isRouteStop && <span className="route-badge">{routeNum}</span>}
                      <span className="bin-card-name">{bin.name}</span>
                    </div>
                    <span className="bin-card-id">{bin.bin_id}</span>
                  </div>
                  <div className="bin-card-bottom">
                    <div className="fill-bar-track">
                      <div
                        className={`fill-bar-fill ${severity}`}
                        style={{ width: `${bin.fill_percent}%` }}
                      />
                    </div>
                    <span className="bin-card-pct" style={{ color: fillColor(bin.fill_percent) }}>
                      {Math.round(bin.fill_percent)}%
                    </span>
                  </div>
                  {isSelected && (
                    <div className="bin-card-detail fade-in">
                      <span>{bin.distance_cm.toFixed(1)} cm</span>
                      <span>{formatTimestamp(bin.ts)}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ---- Map ---- */}
      <div className="map-container">
        {MAPS_KEY ? (
          <APIProvider apiKey={MAPS_KEY}>
            <GoogleMap
              defaultCenter={mapCenter}
              defaultZoom={16}
              mapId="wastewise-map"
              gestureHandling="greedy"
              disableDefaultUI={false}
              style={{ width: "100%", height: "100%" }}
            >
              {bins.map((bin) => (
                <BinMarker
                  key={bin.bin_id}
                  bin={bin}
                  routeOrder={routeOrderMap.get(bin.bin_id)}
                  onClick={() => setSelectedBin(selectedBin === bin.bin_id ? null : bin.bin_id)}
                />
              ))}
            </GoogleMap>
          </APIProvider>
        ) : (
          <div className="loading">
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 8 }}>
                Google Maps API key not set
              </p>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                Add <code>VITE_GOOGLE_MAPS_KEY</code> to your <code>.env</code> file
              </p>
            </div>
          </div>
        )}

        {/* Selected bin overlay */}
        {selected && (
          <div className="map-overlay fade-in">
            <div className="map-overlay-title">Selected Bin</div>
            <div className="map-overlay-name">{selected.name}</div>
            <div className="map-overlay-fill" style={{ color: fillColor(selected.fill_percent) }}>
              {Math.round(selected.fill_percent)}% full
            </div>
            <div className="map-overlay-meta">
              {selected.distance_cm.toFixed(1)} cm &middot; {formatTimestamp(selected.ts)}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="map-legend">
          <div className="legend-item"><div className="legend-dot low" />&lt;35%</div>
          <div className="legend-item"><div className="legend-dot med" />35–59%</div>
          <div className="legend-item"><div className="legend-dot high" />60–84%</div>
          <div className="legend-item"><div className="legend-dot critical" />85%+</div>
        </div>
      </div>
    </div>
  );
}

export default App;
