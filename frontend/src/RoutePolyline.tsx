/// <reference types="@types/google.maps" />
import { useEffect, useRef } from "react";
import { useMap } from "@vis.gl/react-google-maps";

interface RoutePolylineProps {
  path: { lat: number; lng: number }[];
  strokeColor?: string;
  strokeOpacity?: number;
  strokeWeight?: number;
}

export default function RoutePolyline({
  path,
  strokeColor = "#2d6a4f",
  strokeOpacity = 0.8,
  strokeWeight = 3,
}: RoutePolylineProps) {
  const map = useMap();
  const polylineRef = useRef<google.maps.Polyline | null>(null);

  useEffect(() => {
    if (!map) return;

    // Create polyline
    polylineRef.current = new google.maps.Polyline({
      path,
      strokeColor,
      strokeOpacity,
      strokeWeight,
      geodesic: true,
      map,
    });

    // Cleanup on unmount
    return () => {
      if (polylineRef.current) {
        polylineRef.current.setMap(null);
      }
    };
  }, [map, path, strokeColor, strokeOpacity, strokeWeight]);

  // Update polyline when path changes
  useEffect(() => {
    if (polylineRef.current) {
      polylineRef.current.setPath(path);
    }
  }, [path]);

  return null;
}
