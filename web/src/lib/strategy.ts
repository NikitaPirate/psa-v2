import {
  CanonicalPriceSegment,
  CanonicalStrategy,
  CanonicalTimeSegment,
  MarketMode,
} from "./types";

const DEFAULT_MARKET_MODE: MarketMode = "bear";

const DEFAULT_PRICE_SEGMENT: CanonicalPriceSegment = {
  price_low: 30000,
  price_high: 40000,
  weight: 100,
};

const ISO_WITH_TIMEZONE_SUFFIX = /(Z|[+-]\d{2}:\d{2})$/;

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const parseIsoWithTimezone = (value: string): number => {
  if (!ISO_WITH_TIMEZONE_SUFFIX.test(value)) {
    return Number.NaN;
  }
  const ts = Date.parse(value);
  return Number.isFinite(ts) ? ts : Number.NaN;
};

const validatePriceSegments = (segments: CanonicalPriceSegment[]): string[] => {
  if (segments.length === 0) {
    return ["price_segments must contain at least one row"];
  }

  const issues: string[] = [];

  segments.forEach((segment, idx) => {
    if (!isFiniteNumber(segment.price_low) || segment.price_low <= 0) {
      issues.push(`price_segments[${idx}].price_low must be > 0`);
    }
    if (!isFiniteNumber(segment.price_high) || segment.price_high <= 0) {
      issues.push(`price_segments[${idx}].price_high must be > 0`);
    }
    if (
      isFiniteNumber(segment.price_low) &&
      isFiniteNumber(segment.price_high) &&
      segment.price_low >= segment.price_high
    ) {
      issues.push(`price_segments[${idx}] requires price_low < price_high`);
    }
    if (!isFiniteNumber(segment.weight) || segment.weight < 0) {
      issues.push(`price_segments[${idx}].weight must be >= 0`);
    }
  });

  const sorted = [...segments].sort((left, right) => left.price_low - right.price_low);
  for (let idx = 1; idx < sorted.length; idx += 1) {
    const prev = sorted[idx - 1];
    const current = sorted[idx];
    if (current.price_low < prev.price_high) {
      issues.push("price_segments must not overlap");
      break;
    }
  }

  const totalWeight = segments.reduce((acc, row) => acc + row.weight, 0);
  if (!(totalWeight > 0)) {
    issues.push("price_segments total weight must be > 0");
  }

  return issues;
};

const validateTimeSegments = (segments: CanonicalTimeSegment[]): string[] => {
  const issues: string[] = [];

  segments.forEach((segment, idx) => {
    const startTs = parseIsoWithTimezone(segment.start_ts);
    const endTs = parseIsoWithTimezone(segment.end_ts);

    if (!Number.isFinite(startTs)) {
      issues.push(`time_segments[${idx}].start_ts must be ISO with timezone`);
    }
    if (!Number.isFinite(endTs)) {
      issues.push(`time_segments[${idx}].end_ts must be ISO with timezone`);
    }

    if (Number.isFinite(startTs) && Number.isFinite(endTs) && startTs >= endTs) {
      issues.push(`time_segments[${idx}] requires start_ts < end_ts`);
    }

    if (!isFiniteNumber(segment.k_start) || segment.k_start <= 0) {
      issues.push(`time_segments[${idx}].k_start must be > 0`);
    }
    if (!isFiniteNumber(segment.k_end) || segment.k_end <= 0) {
      issues.push(`time_segments[${idx}].k_end must be > 0`);
    }
  });

  const sorted = [...segments].sort(
    (left, right) => Date.parse(left.start_ts) - Date.parse(right.start_ts),
  );

  for (let idx = 1; idx < sorted.length; idx += 1) {
    const prevEndTs = Date.parse(sorted[idx - 1].end_ts);
    const currentStartTs = Date.parse(sorted[idx].start_ts);
    if (currentStartTs < prevEndTs) {
      issues.push("time_segments must not overlap");
      break;
    }
  }

  return issues;
};

export const validateCanonicalStrategy = (strategy: CanonicalStrategy): string[] => {
  const issues: string[] = [];

  if (strategy.market_mode !== "bear" && strategy.market_mode !== "bull") {
    issues.push("market_mode must be 'bear' or 'bull'");
  }

  issues.push(...validatePriceSegments(strategy.price_segments));
  issues.push(...validateTimeSegments(strategy.time_segments));

  return issues;
};

export const buildDefaultStrategy = (): CanonicalStrategy => ({
  market_mode: DEFAULT_MARKET_MODE,
  price_segments: [{ ...DEFAULT_PRICE_SEGMENT }],
  time_segments: [],
});

export const stringifyCanonicalStrategy = (strategy: CanonicalStrategy): string =>
  JSON.stringify(strategy, null, 2);

export const parseCanonicalStrategy = (raw: string): CanonicalStrategy => {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("Input is not valid JSON.");
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Strategy payload must be an object.");
  }

  const payload = parsed as Record<string, unknown>;
  const marketMode = payload.market_mode;
  const priceSegmentsUnknown = payload.price_segments;
  const timeSegmentsUnknown = payload.time_segments;

  if (!Array.isArray(priceSegmentsUnknown)) {
    throw new Error("price_segments must be an array.");
  }

  const priceSegments: CanonicalPriceSegment[] = priceSegmentsUnknown.map((row, idx) => {
    if (!row || typeof row !== "object" || Array.isArray(row)) {
      throw new Error(`price_segments[${idx}] must be an object.`);
    }

    const value = row as Record<string, unknown>;
    if (
      !isFiniteNumber(value.price_low) ||
      !isFiniteNumber(value.price_high) ||
      !isFiniteNumber(value.weight)
    ) {
      throw new Error(
        `price_segments[${idx}] must contain numeric price_low, price_high, weight.`,
      );
    }

    return {
      price_low: value.price_low,
      price_high: value.price_high,
      weight: value.weight,
    };
  });

  let timeSegments: CanonicalTimeSegment[] = [];
  if (timeSegmentsUnknown !== undefined) {
    if (!Array.isArray(timeSegmentsUnknown)) {
      throw new Error("time_segments must be an array.");
    }

    timeSegments = timeSegmentsUnknown.map((row, idx) => {
      if (!row || typeof row !== "object" || Array.isArray(row)) {
        throw new Error(`time_segments[${idx}] must be an object.`);
      }

      const value = row as Record<string, unknown>;
      if (
        typeof value.start_ts !== "string" ||
        typeof value.end_ts !== "string" ||
        !isFiniteNumber(value.k_start) ||
        !isFiniteNumber(value.k_end)
      ) {
        throw new Error(
          `time_segments[${idx}] must contain start_ts, end_ts, k_start, k_end.`,
        );
      }

      return {
        start_ts: value.start_ts,
        end_ts: value.end_ts,
        k_start: value.k_start,
        k_end: value.k_end,
      };
    });
  }

  const strategy: CanonicalStrategy = {
    market_mode: marketMode === "bull" ? "bull" : "bear",
    price_segments: priceSegments,
    time_segments: timeSegments,
  };

  if (marketMode !== "bear" && marketMode !== "bull") {
    throw new Error("market_mode must be 'bear' or 'bull'.");
  }

  const issues = validateCanonicalStrategy(strategy);
  if (issues.length > 0) {
    throw new Error(issues[0]);
  }

  return strategy;
};

export const strategyPriceBounds = (
  strategy: CanonicalStrategy,
): { min: number; max: number } => {
  const values = strategy.price_segments.flatMap((row) => [row.price_low, row.price_high]);
  const min = Math.min(...values);
  const max = Math.max(...values);

  if (!Number.isFinite(min) || !Number.isFinite(max) || min >= max) {
    return { min: 1, max: 100000 };
  }

  return { min, max };
};

const pad2 = (value: number): string => String(value).padStart(2, "0");

export const toLocalDateTimeInput = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}T${pad2(
    date.getHours(),
  )}:${pad2(date.getMinutes())}`;
};

export const fromLocalDateTimeInput = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return new Date().toISOString();
  }
  return date.toISOString();
};

export const cloneStrategy = (strategy: CanonicalStrategy): CanonicalStrategy => ({
  market_mode: strategy.market_mode,
  price_segments: strategy.price_segments.map((row) => ({ ...row })),
  time_segments: strategy.time_segments.map((row) => ({ ...row })),
});
