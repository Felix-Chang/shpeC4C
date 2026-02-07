import { AdvancedMarker } from "@vis.gl/react-google-maps";
import type { BinInfo } from "./types";
import { fillSeverity } from "./utils";

interface BinMarkerProps {
  bin: BinInfo;
  routeOrder?: number; // if part of the route, what stop number
  onClick?: () => void;
}

export default function BinMarker({ bin, routeOrder, onClick }: BinMarkerProps) {
  const severity = fillSeverity(bin.fill_percent);

  return (
    <AdvancedMarker
      position={{ lat: bin.lat, lng: bin.lng }}
      onClick={onClick}
      zIndex={severity === "critical" ? 50 : severity === "high" ? 40 : 10}
    >
      <div className="map-marker">
        {routeOrder !== undefined && (
          <div className="marker-route-badge">{routeOrder}</div>
        )}
        <div className="marker-pin">
          <div className={`marker-pin-bg ${severity}`} />
          <span className="marker-label">{Math.round(bin.fill_percent)}%</span>
        </div>
      </div>
    </AdvancedMarker>
  );
}
