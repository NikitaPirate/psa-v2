export type MarketMode = "bear" | "bull";

export type CanonicalPriceSegment = {
  price_low: number;
  price_high: number;
  weight: number;
};

export type CanonicalTimeSegment = {
  start_ts: string;
  end_ts: string;
  k_start: number;
  k_end: number;
};

export type CanonicalStrategy = {
  market_mode: MarketMode;
  price_segments: CanonicalPriceSegment[];
  time_segments: CanonicalTimeSegment[];
};

export type ObservationRow = {
  timestamp: string;
  price: number;
};

export type EvaluationRow = {
  timestamp: string;
  price: number;
  time_k: number;
  virtual_price: number;
  base_share: number;
  target_share: number;
};

export type EvaluatePointResponse = {
  row: EvaluationRow;
};

export type EvaluateRowsResponse = {
  rows: EvaluationRow[];
};

export type UsePointState = {
  timestamp: string;
  price: number;
  result: EvaluationRow | null;
  error: string;
  isLoading: boolean;
};

export type LinePoint = {
  price: number;
  target_share_pct: number;
  base_share_pct: number;
};

export type HeatmapSurfaceData = {
  time_iso: string[];
  day_offsets: number[];
  prices_desc: number[];
  z_target_share_pct: Array<Array<number | null>>;
  tick_vals: number[];
  tick_text: string[];
};

export type ChartDataBundle = {
  line_points: LinePoint[];
  heatmap_surface: HeatmapSurfaceData | null;
  heatmap_status: string;
};

export type ApiErrorEnvelope = {
  error?: {
    message?: string;
  };
};
