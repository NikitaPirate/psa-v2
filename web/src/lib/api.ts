import {
  ApiErrorEnvelope,
  CanonicalStrategy,
  EvaluatePortfolioResponse,
  EvaluatePointResponse,
  EvaluateRowsResponse,
  ObservationRow,
} from "./types";

const API_BASE = "/v1";

type EvaluateRowsFromRangesRequest = {
  price_start: number;
  price_end: number;
  price_steps: number;
  time_start: string;
  time_end: string;
  time_steps: number;
  include_price_breakpoints: boolean;
};

type EvaluatePortfolioRequest = {
  timestamp: string;
  price: number;
  usd_amount: number;
  asset_amount: number;
  avg_entry_price?: number | null;
  alignment_search_min_price?: number;
  alignment_search_max_price?: number;
};

const getApiError = (body: unknown, status: number): string => {
  if (typeof body === "object" && body !== null) {
    const envelope = body as ApiErrorEnvelope;
    if (envelope.error?.message) {
      return envelope.error.message;
    }
  }
  return `API request failed with status ${status}.`;
};

async function postJson<TResponse>(
  path: string,
  payload: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  const body = await response.json();

  if (!response.ok) {
    throw new Error(getApiError(body, response.status));
  }

  return body as TResponse;
}

export async function evaluatePoint(
  strategy: CanonicalStrategy,
  timestamp: string,
  price: number,
  signal?: AbortSignal,
): Promise<EvaluatePointResponse> {
  return postJson<EvaluatePointResponse>(
    "/evaluate/point",
    {
      strategy,
      timestamp,
      price,
    },
    signal,
  );
}

export async function evaluateRows(
  strategy: CanonicalStrategy,
  rows: ObservationRow[],
  signal?: AbortSignal,
): Promise<EvaluateRowsResponse> {
  return postJson<EvaluateRowsResponse>(
    "/evaluate/rows",
    {
      strategy,
      rows,
    },
    signal,
  );
}

export async function evaluateRowsFromRanges(
  strategy: CanonicalStrategy,
  request: EvaluateRowsFromRangesRequest,
  signal?: AbortSignal,
): Promise<EvaluateRowsResponse> {
  return postJson<EvaluateRowsResponse>(
    "/evaluate/rows-from-ranges",
    {
      strategy,
      ...request,
    },
    signal,
  );
}

export async function evaluatePortfolio(
  strategy: CanonicalStrategy,
  request: EvaluatePortfolioRequest,
  signal?: AbortSignal,
): Promise<EvaluatePortfolioResponse> {
  return postJson<EvaluatePortfolioResponse>(
    "/evaluate/portfolio",
    {
      strategy,
      ...request,
    },
    signal,
  );
}
