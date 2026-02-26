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

export type PortfolioEvaluation = {
  timestamp: string;
  price: number;
  time_k: number;
  virtual_price: number;
  base_share: number;
  target_share: number;
  share_deviation: number;
  portfolio_value_usd: number;
  asset_value_usd: number;
  usd_value_usd: number;
  target_asset_value_usd: number;
  target_asset_amount: number;
  asset_amount_delta: number;
  usd_delta: number;
  alignment_price: number | null;
  avg_entry_price: number | null;
  avg_entry_pnl_usd: number | null;
  avg_entry_pnl_pct: number | null;
};

export type EvaluatePortfolioResponse = {
  portfolio: PortfolioEvaluation;
};

export type UsePointState = {
  timestamp: string;
  price: number;
  result: EvaluationRow | null;
  error: string;
  isLoading: boolean;
};

export type UsePortfolioState = {
  timestamp: string;
  price: number;
  usd_amount: number;
  asset_amount: number;
  avg_entry_price: number | null;
  result: PortfolioEvaluation | null;
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
