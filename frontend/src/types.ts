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
