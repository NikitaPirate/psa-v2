import { ChartDataBundle, EvaluationRow, HeatmapSurfaceData, LinePoint, ObservationRow } from "./types";

const DAY_MS = 24 * 60 * 60 * 1000;

const dedupeSorted = (values: number[]): number[] => {
  const sorted = [...values].sort((left, right) => left - right);
  const result: number[] = [];

  sorted.forEach((value) => {
    if (result.length === 0 || Math.abs(value - result[result.length - 1]) > 1e-9) {
      result.push(value);
    }
  });

  return result;
};

export const buildPriceGrid = (
  segments: Array<{ price_low: number; price_high: number }>,
  steps = 60,
): number[] => {
  const lows = segments.map((row) => row.price_low);
  const highs = segments.map((row) => row.price_high);
  const min = Math.min(...lows);
  const max = Math.max(...highs);

  const spanPoints = Array.from({ length: Math.max(steps, 2) }, (_, idx) => {
    if (steps <= 1) {
      return min;
    }
    return min + ((max - min) * idx) / (steps - 1);
  });

  const boundaries = segments.flatMap((row) => [row.price_low, row.price_high]);
  return dedupeSorted([...spanPoints, ...boundaries]);
};

export const buildObservationRows = (timestamp: string, prices: number[]): ObservationRow[] =>
  prices.map((price) => ({ timestamp, price }));

export const buildLinePoints = (rows: EvaluationRow[]): LinePoint[] =>
  [...rows]
    .sort((left, right) => left.price - right.price)
    .map((row) => ({
      price: row.price,
      target_share_pct: row.target_share * 100,
      base_share_pct: row.base_share * 100,
    }));

const formatCompactDate = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }

  const month = date.toLocaleString("en-US", { month: "short" }).toLowerCase();
  const day = String(date.getDate()).padStart(2, "0");
  return `${day}-${month}-${date.getFullYear()}`;
};

const buildTickIndexes = (length: number, maxTicks = 7): number[] => {
  if (length <= 0) {
    return [];
  }

  if (length <= maxTicks) {
    return Array.from({ length }, (_, idx) => idx);
  }

  const step = Math.max(1, Math.floor((length - 1) / (maxTicks - 1)));
  const indexes = Array.from({ length }, (_, idx) => idx).filter((idx) => idx % step === 0);
  if (indexes[indexes.length - 1] !== length - 1) {
    indexes.push(length - 1);
  }
  return indexes;
};

export const buildHeatmapSurfaceData = (
  rows: EvaluationRow[],
  nowIso: string,
): HeatmapSurfaceData => {
  const timeSet = new Set<string>();
  const priceSet = new Set<number>();
  const valueMap = new Map<string, number>();

  rows.forEach((row) => {
    timeSet.add(row.timestamp);
    priceSet.add(row.price);
    valueMap.set(`${row.timestamp}::${row.price}`, row.target_share * 100);
  });

  const timeIso = Array.from(timeSet).sort();
  const pricesDesc = Array.from(priceSet).sort((left, right) => right - left);

  const anchor = new Date(nowIso);
  anchor.setHours(0, 0, 0, 0);
  const anchorMs = anchor.getTime();

  const dayOffsets = timeIso.map((time) => {
    const ts = Date.parse(time);
    if (!Number.isFinite(ts) || !Number.isFinite(anchorMs)) {
      return 0;
    }
    return (ts - anchorMs) / DAY_MS;
  });

  const zTargetSharePct = pricesDesc.map((price) =>
    timeIso.map((time) => {
      const value = valueMap.get(`${time}::${price}`);
      return value ?? null;
    }),
  );

  const tickIndexes = buildTickIndexes(dayOffsets.length);

  return {
    time_iso: timeIso,
    day_offsets: dayOffsets,
    prices_desc: pricesDesc,
    z_target_share_pct: zTargetSharePct,
    tick_vals: tickIndexes.map((idx) => dayOffsets[idx]),
    tick_text: tickIndexes.map((idx) => formatCompactDate(timeIso[idx])),
  };
};

export const emptyChartBundle = (): ChartDataBundle => ({
  line_points: [],
  heatmap_surface: null,
  heatmap_status: "",
});
