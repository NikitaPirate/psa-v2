import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";

type PriceSegment = {
  price_low: number;
  price_high: number;
  weight: number;
};

type StrategyPayload = {
  market_mode: "bear" | "bull";
  price_segments: PriceSegment[];
  time_segments?: Array<Record<string, unknown>>;
};

type EvaluatePointResponse = {
  row: {
    timestamp: string;
    price: number;
    time_k: number;
    virtual_price: number;
    base_share: number;
    target_share: number;
  };
};

const EVALUATE_POINT_API_URL = "/v1/evaluate/point";
const DEFAULT_PRICE_MIN = 1;
const DEFAULT_PRICE_MAX = 100_000;
const DEFAULT_PRICE = 50_000;
// POC only: fixed timestamp to minimize scope and prove JSON transfer + evaluate flow.
const POC_TIMESTAMP = "2026-01-01T00:00:00Z";

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function parseStrategyPayload(rawText: string): StrategyPayload {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawText);
  } catch {
    throw new Error("Input is not valid JSON.");
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Strategy JSON must be an object.");
  }

  const payload = parsed as Record<string, unknown>;
  const marketMode = payload.market_mode;
  if (marketMode !== "bear" && marketMode !== "bull") {
    throw new Error("market_mode must be 'bear' or 'bull'.");
  }

  const priceSegments = payload.price_segments;
  if (!Array.isArray(priceSegments) || priceSegments.length === 0) {
    throw new Error("price_segments must be a non-empty array.");
  }

  for (let idx = 0; idx < priceSegments.length; idx += 1) {
    const segment = priceSegments[idx];
    if (!segment || typeof segment !== "object" || Array.isArray(segment)) {
      throw new Error(`price_segments[${idx}] must be an object.`);
    }
    const row = segment as Record<string, unknown>;
    if (!isFiniteNumber(row.price_low) || !isFiniteNumber(row.price_high)) {
      throw new Error(`price_segments[${idx}] must include numeric price_low/price_high.`);
    }
    if (!isFiniteNumber(row.weight)) {
      throw new Error(`price_segments[${idx}] must include numeric weight.`);
    }
  }

  return payload as unknown as StrategyPayload;
}

function getPriceBounds(strategy: StrategyPayload): { min: number; max: number } {
  const values = strategy.price_segments.flatMap((segment) => [segment.price_low, segment.price_high]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (!Number.isFinite(min) || !Number.isFinite(max) || min >= max) {
    return { min: DEFAULT_PRICE_MIN, max: DEFAULT_PRICE_MAX };
  }
  return { min, max };
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error.";
}

function formatShare(value: number): string {
  return value.toFixed(6);
}

function readFileAsText(file: File): Promise<string> {
  if (typeof file.text === "function") {
    return file.text();
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("Failed to read file."));
    reader.readAsText(file);
  });
}

export function App() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [jsonText, setJsonText] = useState<string>("");
  const [strategy, setStrategy] = useState<StrategyPayload | null>(null);
  const [parseStatus, setParseStatus] = useState<string>("");
  const [parseError, setParseError] = useState<string>("");
  const [priceRange, setPriceRange] = useState({ min: DEFAULT_PRICE_MIN, max: DEFAULT_PRICE_MAX });
  const [price, setPrice] = useState<number>(DEFAULT_PRICE);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalError, setEvalError] = useState("");
  const [result, setResult] = useState<EvaluatePointResponse["row"] | null>(null);

  const canEvaluate = strategy !== null;

  useEffect(() => {
    if (!strategy) {
      setResult(null);
      return;
    }

    const controller = new AbortController();
    const run = async () => {
      setIsEvaluating(true);
      setEvalError("");

      try {
        const response = await fetch(EVALUATE_POINT_API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            strategy,
            timestamp: POC_TIMESTAMP,
            price,
          }),
          signal: controller.signal,
        });

        const body = (await response.json()) as EvaluatePointResponse | { error?: { message?: string } };
        if (!response.ok) {
          const message =
            typeof body === "object" && body && "error" in body && body.error?.message
              ? body.error.message
              : `API request failed with status ${response.status}.`;
          throw new Error(message);
        }

        if (!("row" in body)) {
          throw new Error("API response does not contain row.");
        }

        setResult(body.row);
      } catch (error) {
        if (!controller.signal.aborted) {
          setResult(null);
          setEvalError(getErrorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsEvaluating(false);
        }
      }
    };

    void run();
    return () => controller.abort();
  }, [price, strategy]);

  const rangeLabel = useMemo(() => `${priceRange.min} .. ${priceRange.max}`, [priceRange]);

  function handleParse() {
    try {
      const parsedStrategy = parseStrategyPayload(jsonText);
      const bounds = getPriceBounds(parsedStrategy);
      const nextPrice = Math.min(Math.max(price, bounds.min), bounds.max);

      setStrategy(parsedStrategy);
      setPriceRange(bounds);
      setPrice(nextPrice);
      setParseError("");
      setParseStatus("Parsed successfully.");
    } catch (error) {
      setStrategy(null);
      setParseStatus("");
      setResult(null);
      setEvalError("");
      setPriceRange({ min: DEFAULT_PRICE_MIN, max: DEFAULT_PRICE_MAX });
      setParseError(getErrorMessage(error));
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(jsonText);
      setParseError("");
      setParseStatus("JSON copied to clipboard.");
    } catch {
      setParseStatus("");
      setParseError("Clipboard copy failed.");
    }
  }

  function handleDownload() {
    const blob = new Blob([jsonText], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "strategy.json";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function handleFileUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const text = await readFileAsText(file);
    setJsonText(text);
    setParseStatus("File loaded into JSON field.");
    setParseError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <main>
      <h1>PSA Transfer &amp; Evaluate POC</h1>
      <p>
        One canonical strategy JSON for web/agent/cli. Paste or upload strategy payload, parse it,
        then move price slider to evaluate <code>target_share</code>.
      </p>

      <section className="card">
        <label htmlFor="strategy-json">Strategy JSON (canonical payload)</label>
        <textarea
          id="strategy-json"
          value={jsonText}
          onChange={(event) => setJsonText(event.target.value)}
          placeholder='{"market_mode":"bear","price_segments":[{"price_low":30000,"price_high":40000,"weight":1}]}'
        />

        <div className="controls">
          <button type="button" onClick={handleParse}>
            Parse
          </button>
          <button type="button" onClick={() => void handleCopy()}>
            Copy
          </button>
          <button type="button" onClick={handleDownload}>
            Download .json
          </button>
          <label className="button-label" htmlFor="upload-json">
            Upload .json
            <input
              id="upload-json"
              ref={fileInputRef}
              type="file"
              accept=".json,application/json"
              onChange={(event) => void handleFileUpload(event)}
            />
          </label>
        </div>

        <div className={parseError ? "status error" : "status ok"}>
          {parseError || parseStatus}
        </div>

        <div className="slider-wrap">
          <div className="meta">Price range: {rangeLabel}</div>
          <div className="slider-row">
            <input
              type="range"
              min={priceRange.min}
              max={priceRange.max}
              step="1"
              value={price}
              disabled={!canEvaluate}
              onChange={(event) => setPrice(Number(event.target.value))}
            />
            <output>{price}</output>
          </div>
        </div>

        {isEvaluating && <div className="meta">Evaluating...</div>}
        {evalError && <div className="status error">{evalError}</div>}

        {result && (
          <div className="result">
            <div>
              target_share: <strong>{formatShare(result.target_share)}</strong>
            </div>
            <div>base_share: {formatShare(result.base_share)}</div>
            <div className="meta">timestamp: {POC_TIMESTAMP}</div>
          </div>
        )}
      </section>
    </main>
  );
}
