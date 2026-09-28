export type VarCode = "t2m" | "tp" | "z500" | "ws850";
export type LayerCode = "confidence" | "p_bust" | "error";
export type ExportFormat = "geojson" | "geotiff" | "netcdf";

export type Latitude = number;
export type Longitude = number;
export type LeadTime = number;
export type Probability = number;
export type Confidence = number;

export type BBox = [Longitude, Latitude, Longitude, Latitude];

export interface GridMeta {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
  resolution: number;
  n_rows: number;
  n_cols: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type SourceModel = "GFS" | "ECMWF" | "SYNTHETIC";
export type RunStatus = "PENDING" | "RUNNING" | "COMPLETE" | "FAILED";

export interface ForecastRunSummary {
  run_id: string;
  init_time: string; // ISO datetime
  source_model: SourceModel;
  n_lead_times: number;
  created_at: string;
  mean_confidence: Confidence;
}

export interface ForecastRunDetail extends ForecastRunSummary {
  grid: GridMeta;
  variables: VarCode[];
  norm_stats_ref: string;
}

export interface ConfidenceMapResponse {
  run_id: string;
  lead_time: LeadTime;
  grid: GridMeta;
  values: Confidence[][]; // 128x128 row-major, north-up
  stats: Record<string, number>;
}

export interface BustProbabilityRequest {
  run_id: string;
  variables?: VarCode[];
  lead_times?: LeadTime[];
  bbox?: BBox;
}

export interface BustProbabilityLayer {
  variable: VarCode;
  lead_time: LeadTime;
  values: Probability[][];
  threshold: number;
  bust_frequency: number;
}

export interface BustProbabilityResponse {
  run_id: string;
  grid: GridMeta;
  layers: BustProbabilityLayer[];
}

export interface BustDetection {
  detection_id: string;
  run_id: string;
  variable: VarCode;
  lead_time: LeadTime;
  bbox: BBox;
  polygon: any; // GeoJSON
  peak_probability: Probability;
  mean_probability: Probability;
  area_km2: number;
  dominant_driver: string;
  confidence: Confidence;
  created_at: string;
}

export interface BaselineStats {
  mean_rmse: number;
  mean_mae: number;
  bust_frequency: number;
  p90_abs_error: number;
  std_abs_error?: number;
}

export interface BaselinePeriod {
  start: string;
  end: string;
}

export interface HistoricalBaseline {
  baseline_id: string;
  region_label: string;
  region_geometry: any;
  variable: VarCode;
  lead_time: LeadTime;
  sample_count: number;
  period: BaselinePeriod;
  stats: BaselineStats;
  threshold?: number;
  created_at: string;
}

export interface DriverAttribution {
  channel_code: string;
  channel_name: string;
  score: number;
  sign: "+" | "-";
}

export interface AttributionResponse {
  run_id: string;
  variable: VarCode;
  lead_time: LeadTime;
  lat: Latitude;
  lon: Longitude;
  drivers: DriverAttribution[];
  spatial_gradcam: number[][]; // 128x128
  narrative: string;
}

export type TelemetryKind = "INFERENCE" | "ALERT" | "EXPORT" | "ERROR";
export type TelemetrySeverity = "INFO" | "WARN" | "CRITICAL";

export interface TelemetryEvent {
  event_id: string;
  kind: TelemetryKind;
  severity: TelemetrySeverity;
  run_id?: string;
  message: string;
  latency_ms?: number;
  created_at: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  version: string;
  mongo: "up" | "down";
  model_loaded: boolean;
  uptime_s: number;
}
