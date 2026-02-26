import { CanonicalStrategy } from "./types";
import { parseCanonicalStrategy } from "./strategy";

export type AppMode = "create" | "use";

export type UseDraftState = {
  now_price_input: number;
  custom_timestamp_input: string;
  custom_price_input: number;
  portfolio_timestamp_input: string;
  portfolio_price_input: number;
  portfolio_usd_input: number;
  portfolio_asset_input: number;
  portfolio_avg_entry_price_input: string;
};

export type PersistedWebStateV1 = {
  version: 1;
  saved_at: string;
  strategy: CanonicalStrategy;
  use_draft?: UseDraftState;
  ui?: {
    mode: AppMode;
    chart_timestamp: string;
  };
};

export const PERSISTED_WEB_STATE_VERSION = 1;
export const PERSISTED_WEB_STATE_STORAGE_KEY = "psa:web:state:v1";

const hasWindowStorage = (): boolean =>
  typeof window !== "undefined" && typeof window.localStorage !== "undefined";

const isObjectRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const isString = (value: unknown): value is string => typeof value === "string";

const parseStrategy = (value: unknown): CanonicalStrategy | null => {
  try {
    return parseCanonicalStrategy(JSON.stringify(value));
  } catch {
    return null;
  }
};

export function loadPersistedState(): PersistedWebStateV1 | null {
  if (!hasWindowStorage()) {
    return null;
  }

  let raw: string | null;
  try {
    raw = window.localStorage.getItem(PERSISTED_WEB_STATE_STORAGE_KEY);
  } catch {
    return null;
  }

  if (!raw) {
    return null;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }

  if (!isObjectRecord(parsed)) {
    return null;
  }

  if (parsed.version !== PERSISTED_WEB_STATE_VERSION) {
    return null;
  }

  const strategy = parseStrategy(parsed.strategy);
  if (!strategy) {
    return null;
  }

  if (!isString(parsed.saved_at)) {
    return null;
  }

  let useDraft: UseDraftState | undefined;
  if (parsed.use_draft !== undefined) {
    const draftRaw = parsed.use_draft;
    if (
      !isObjectRecord(draftRaw) ||
      !isFiniteNumber(draftRaw.now_price_input) ||
      !isString(draftRaw.custom_timestamp_input) ||
      !isFiniteNumber(draftRaw.custom_price_input) ||
      !isString(draftRaw.portfolio_timestamp_input) ||
      !isFiniteNumber(draftRaw.portfolio_price_input) ||
      !isFiniteNumber(draftRaw.portfolio_usd_input) ||
      !isFiniteNumber(draftRaw.portfolio_asset_input) ||
      !isString(draftRaw.portfolio_avg_entry_price_input)
    ) {
      return null;
    }

    useDraft = {
      now_price_input: draftRaw.now_price_input,
      custom_timestamp_input: draftRaw.custom_timestamp_input,
      custom_price_input: draftRaw.custom_price_input,
      portfolio_timestamp_input: draftRaw.portfolio_timestamp_input,
      portfolio_price_input: draftRaw.portfolio_price_input,
      portfolio_usd_input: draftRaw.portfolio_usd_input,
      portfolio_asset_input: draftRaw.portfolio_asset_input,
      portfolio_avg_entry_price_input: draftRaw.portfolio_avg_entry_price_input,
    };
  }

  let ui: PersistedWebStateV1["ui"];
  if (parsed.ui !== undefined) {
    const uiRaw = parsed.ui;
    if (
      !isObjectRecord(uiRaw) ||
      (uiRaw.mode !== "create" && uiRaw.mode !== "use") ||
      !isString(uiRaw.chart_timestamp)
    ) {
      return null;
    }

    ui = {
      mode: uiRaw.mode,
      chart_timestamp: uiRaw.chart_timestamp,
    };
  }

  return {
    version: 1,
    saved_at: parsed.saved_at,
    strategy,
    use_draft: useDraft,
    ui,
  };
}

export function savePersistedState(state: PersistedWebStateV1): void {
  if (!hasWindowStorage()) {
    return;
  }

  try {
    window.localStorage.setItem(PERSISTED_WEB_STATE_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Keep UI responsive when localStorage is unavailable or quota is exceeded.
  }
}
