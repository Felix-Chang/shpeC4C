export interface BinInfo {
  bin_id: string;
  name: string;
  lat: number;
  lng: number;
  distance_cm: number;
  fill_percent: number;
  ts: number;
}

export type RoutePoint = {
  bin: BinInfo;
  order: number;
};

export interface RouteStop {
  bin_id: string;
  name: string;
  lat: number;
  lng: number;
  fill_percent: number;
  priority: number;
  order: number;
}

export interface RouteOut {
  stops: RouteStop[];
  polyline: [number, number][]; // Array of [lat, lng] pairs
}
