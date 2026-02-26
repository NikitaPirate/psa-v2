import { ChangeEvent, useEffect, useMemo, useState } from "react";
import {
  evaluatePoint,
  evaluatePortfolio,
  evaluateRows,
  evaluateRowsFromRanges,
} from "./lib/api";
import {
  buildDefaultStrategy,
  cloneStrategy,
  parseCanonicalStrategy,
  strategyPriceBounds,
  stringifyCanonicalStrategy,
  validateCanonicalStrategy,
} from "./lib/strategy";
import {
  buildHeatmapSurfaceData,
  buildLinePoints,
  buildObservationRows,
  buildPriceGrid,
  emptyChartBundle,
} from "./lib/charts";
import {
  CanonicalStrategy,
  UsePortfolioState,
  UsePointState,
} from "./lib/types";
import {
  normalizeWeightsToHundred,
  rebalanceWeightsAfterEdit,
  rebalanceWeightsAfterRemoval,
  sumWeights,
  weightTotalTarget,
} from "./lib/weights";
import { CreateScreen } from "./components/CreateScreen";
import { UseScreen } from "./components/UseScreen";

type Mode = "create" | "use";

const CHART_DEBOUNCE_MS = 320;
const CHART_PRICE_STEPS = 31;
const CHART_TIME_STEPS = 24;
const MIN_OBSERVATION_PRICE = 0.01;

const nowIso = (): string => new Date().toISOString();
const randomId = (): string =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
const initialModeFromLocation = (): Mode => {
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") === "use" ? "use" : "create";
};

function sanitizeNumber(value: number, fallback = 0): number {
  if (!Number.isFinite(value)) {
    return fallback;
  }
  return value;
}

function sanitizePositivePrice(value: number): number {
  const sanitized = sanitizeNumber(value, MIN_OBSERVATION_PRICE);
  return sanitized > 0 ? sanitized : MIN_OBSERVATION_PRICE;
}

function sanitizeNonNegativeNumber(value: number, fallback = 0): number {
  const sanitized = sanitizeNumber(value, fallback);
  return sanitized >= 0 ? sanitized : 0;
}

function maxTimeSegmentEnd(strategy: CanonicalStrategy): string | null {
  if (strategy.time_segments.length === 0) {
    return null;
  }

  const sorted = [...strategy.time_segments].sort(
    (left, right) => Date.parse(left.end_ts) - Date.parse(right.end_ts),
  );

  return sorted[sorted.length - 1].end_ts;
}

function downloadJson(filename: string, content: string): void {
  const blob = new Blob([content], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function initialUsePoint(price: number): UsePointState {
  return {
    timestamp: nowIso(),
    price,
    result: null,
    error: "",
    isLoading: false,
  };
}

function initialUsePortfolio(price: number): UsePortfolioState {
  return {
    timestamp: nowIso(),
    price,
    usd_amount: 10_000,
    asset_amount: 0.25,
    avg_entry_price: null,
    result: null,
    error: "",
    isLoading: false,
  };
}

export function App() {
  const [mode, setMode] = useState<Mode>(initialModeFromLocation);
  const [strategy, setStrategy] = useState<CanonicalStrategy>(buildDefaultStrategy);

  const bounds = useMemo(() => strategyPriceBounds(strategy), [strategy]);

  const [jsonText, setJsonText] = useState<string>(() =>
    stringifyCanonicalStrategy(buildDefaultStrategy()),
  );
  const [jsonStatus, setJsonStatus] = useState("");
  const [jsonError, setJsonError] = useState("");
  const [lockedPriceSegmentIds, setLockedPriceSegmentIds] = useState<string[]>([]);
  const [priceSegmentIds, setPriceSegmentIds] = useState<string[]>(() =>
    buildDefaultStrategy().price_segments.map(() => randomId()),
  );

  const [chartTimestamp, setChartTimestamp] = useState<string>(() => nowIso());

  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState("");
  const [charts, setCharts] = useState(emptyChartBundle);

  const [nowPriceInput, setNowPriceInput] = useState<number>(() =>
    Math.round((bounds.min + bounds.max) / 2),
  );
  const [customTimestampInput, setCustomTimestampInput] = useState<string>(() => nowIso());
  const [customPriceInput, setCustomPriceInput] = useState<number>(() =>
    Math.round((bounds.min + bounds.max) / 2),
  );

  const [nowPoint, setNowPoint] = useState<UsePointState>(() => initialUsePoint(nowPriceInput));
  const [customPoint, setCustomPoint] = useState<UsePointState>(() => ({
    ...initialUsePoint(customPriceInput),
    timestamp: customTimestampInput,
  }));
  const [portfolioTimestampInput, setPortfolioTimestampInput] = useState<string>(() => nowIso());
  const [portfolioPriceInput, setPortfolioPriceInput] = useState<number>(() =>
    Math.round((bounds.min + bounds.max) / 2),
  );
  const [portfolioUsdInput, setPortfolioUsdInput] = useState<number>(10_000);
  const [portfolioAssetInput, setPortfolioAssetInput] = useState<number>(0.25);
  const [portfolioAvgEntryPriceInput, setPortfolioAvgEntryPriceInput] = useState<string>("");
  const [portfolioState, setPortfolioState] = useState<UsePortfolioState>(() =>
    initialUsePortfolio(Math.round((bounds.min + bounds.max) / 2)),
  );

  const validationIssues = useMemo(() => validateCanonicalStrategy(strategy), [strategy]);
  const weightTarget = weightTotalTarget();
  const priceWeightRows = useMemo(
    () =>
      strategy.price_segments.map((row, index) => ({
        id: priceSegmentIds[index] ?? `missing-${index}`,
        weight: row.weight,
      })),
    [priceSegmentIds, strategy.price_segments],
  );
  const priceWeightTotal = useMemo(() => sumWeights(priceWeightRows), [priceWeightRows]);
  const lockedPriceSegmentIdSet = useMemo(
    () => new Set(lockedPriceSegmentIds),
    [lockedPriceSegmentIds],
  );

  useEffect(() => {
    setJsonText(stringifyCanonicalStrategy(strategy));
  }, [strategy]);

  useEffect(() => {
    setPriceSegmentIds((current) => {
      const next = strategy.price_segments.map((_, idx) => current[idx] ?? randomId());
      return next;
    });
  }, [strategy.price_segments.length]);

  useEffect(() => {
    const activeIds = new Set(priceSegmentIds);
    setLockedPriceSegmentIds((current) => current.filter((id) => activeIds.has(id)));
  }, [priceSegmentIds]);

  useEffect(() => {
    const nextMid = Math.round((bounds.min + bounds.max) / 2);

    setNowPriceInput((current) =>
      Math.min(Math.max(current, bounds.min), bounds.max) || nextMid,
    );
    setCustomPriceInput((current) =>
      Math.min(Math.max(current, bounds.min), bounds.max) || nextMid,
    );
    setPortfolioPriceInput((current) =>
      Math.min(Math.max(current, bounds.min), bounds.max) || nextMid,
    );
  }, [bounds.max, bounds.min]);

  useEffect(() => {
    const abort = new AbortController();
    const timer = window.setTimeout(() => {
      if (validationIssues.length > 0) {
        setChartLoading(false);
        setChartError(validationIssues[0]);
        setCharts(emptyChartBundle());
        return;
      }

      const parsedTimestamp = Date.parse(chartTimestamp);
      if (!Number.isFinite(parsedTimestamp)) {
        setChartLoading(false);
        setChartError("Chart timestamp is invalid.");
        setCharts(emptyChartBundle());
        return;
      }

      const run = async () => {
        setChartLoading(true);
        setChartError("");

        try {
          const linePrices = buildPriceGrid(strategy.price_segments, 60);
          const lineRows = buildObservationRows(chartTimestamp, linePrices);

          const lineResponse = await evaluateRows(strategy, lineRows, abort.signal);
          const linePoints = buildLinePoints(lineResponse.rows);

          let heatmapSurface = null;
          let heatmapStatus = "No time segments";

          if (strategy.time_segments.length > 0) {
            const timeStart = nowIso();
            const timeEnd = maxTimeSegmentEnd(strategy);

            if (!timeEnd || Date.parse(timeEnd) <= Date.parse(timeStart)) {
              heatmapStatus = "No future time segments";
            } else {
              const rangeResponse = await evaluateRowsFromRanges(
                strategy,
                {
                  price_start: bounds.max,
                  price_end: bounds.min,
                  price_steps: CHART_PRICE_STEPS,
                  time_start: timeStart,
                  time_end: timeEnd,
                  time_steps: CHART_TIME_STEPS,
                  include_price_breakpoints: true,
                },
                abort.signal,
              );
              heatmapSurface = buildHeatmapSurfaceData(rangeResponse.rows, timeStart);
              heatmapStatus = "";
            }
          }

          if (!abort.signal.aborted) {
            setCharts({
              line_points: linePoints,
              heatmap_surface: heatmapSurface,
              heatmap_status: heatmapStatus,
            });
          }
        } catch (error) {
          if (!abort.signal.aborted) {
            setCharts(emptyChartBundle());
            setChartError(error instanceof Error ? error.message : "Chart request failed.");
          }
        } finally {
          if (!abort.signal.aborted) {
            setChartLoading(false);
          }
        }
      };

      void run();
    }, CHART_DEBOUNCE_MS);

    return () => {
      abort.abort();
      window.clearTimeout(timer);
    };
  }, [
    bounds.max,
    bounds.min,
    chartTimestamp,
    strategy,
    validationIssues,
  ]);

  const updateStrategy = (updater: (current: CanonicalStrategy) => CanonicalStrategy) => {
    setStrategy((current) => updater(cloneStrategy(current)));
    setJsonStatus("");
    setJsonError("");
  };

  const onApplyJson = () => {
    try {
      const parsed = parseCanonicalStrategy(jsonText);
      const normalizedRows = normalizeWeightsToHundred(
        parsed.price_segments.map((row, index) => ({
          id: `parsed-${index}`,
          weight: row.weight,
        })),
      );
      const normalizedStrategy: CanonicalStrategy = {
        ...parsed,
        price_segments: parsed.price_segments.map((row, index) => ({
          ...row,
          weight: normalizedRows[index].weight,
        })),
      };
      setStrategy(normalizedStrategy);
      setLockedPriceSegmentIds([]);
      setPriceSegmentIds(normalizedStrategy.price_segments.map(() => randomId()));
      setJsonError("");
      setJsonStatus("JSON applied.");
    } catch (error) {
      setJsonStatus("");
      setJsonError(error instanceof Error ? error.message : "Failed to apply JSON.");
    }
  };

  const onSaveJson = () => {
    downloadJson("strategy.json", stringifyCanonicalStrategy(strategy));
    setJsonError("");
    setJsonStatus("JSON saved.");
  };

  const onUploadJson = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      setJsonText(text);
      setJsonError("");
      setJsonStatus("File loaded.");
    } catch {
      setJsonStatus("");
      setJsonError("File read failed.");
    }

    event.target.value = "";
  };

  const evaluateNow = async () => {
    if (validationIssues.length > 0) {
      setNowPoint((current) => ({
        ...current,
        error: validationIssues[0],
        isLoading: false,
      }));
      return;
    }

    const timestamp = nowIso();
    const price = sanitizePositivePrice(nowPriceInput);
    setNowPoint((current) => ({
      ...current,
      timestamp,
      price,
      error: "",
      isLoading: true,
    }));

    try {
      const response = await evaluatePoint(strategy, timestamp, price);
      setNowPoint({
        timestamp,
        price,
        result: response.row,
        error: "",
        isLoading: false,
      });
    } catch (error) {
      setNowPoint((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Point evaluation failed.",
        isLoading: false,
      }));
    }
  };

  const evaluateCustom = async () => {
    if (validationIssues.length > 0) {
      setCustomPoint((current) => ({
        ...current,
        error: validationIssues[0],
        isLoading: false,
      }));
      return;
    }

    const timestamp = customTimestampInput;
    const price = sanitizePositivePrice(customPriceInput);

    setCustomPoint((current) => ({
      ...current,
      timestamp,
      price,
      error: "",
      isLoading: true,
    }));

    try {
      const response = await evaluatePoint(strategy, timestamp, price);
      setCustomPoint({
        timestamp,
        price,
        result: response.row,
        error: "",
        isLoading: false,
      });
    } catch (error) {
      setCustomPoint((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Point evaluation failed.",
        isLoading: false,
      }));
    }
  };

  const evaluatePortfolioSnapshot = async () => {
    if (validationIssues.length > 0) {
      setPortfolioState((current) => ({
        ...current,
        error: validationIssues[0],
        isLoading: false,
      }));
      return;
    }

    const timestamp = portfolioTimestampInput;
    const price = sanitizePositivePrice(portfolioPriceInput);
    const usdAmount = sanitizeNonNegativeNumber(portfolioUsdInput);
    const assetAmount = sanitizeNonNegativeNumber(portfolioAssetInput);
    const avgEntryRaw = portfolioAvgEntryPriceInput.trim();

    let avgEntryPrice: number | null = null;
    if (avgEntryRaw.length > 0) {
      const parsedAvg = Number(avgEntryRaw);
      if (!Number.isFinite(parsedAvg) || parsedAvg <= 0) {
        setPortfolioState((current) => ({
          ...current,
          error: "Average entry price must be > 0.",
          isLoading: false,
        }));
        return;
      }
      avgEntryPrice = parsedAvg;
    }

    if (usdAmount === 0 && assetAmount === 0) {
      setPortfolioState((current) => ({
        ...current,
        error: "USD and asset amounts cannot both be zero.",
        isLoading: false,
      }));
      return;
    }

    setPortfolioState((current) => ({
      ...current,
      timestamp,
      price,
      usd_amount: usdAmount,
      asset_amount: assetAmount,
      avg_entry_price: avgEntryPrice,
      error: "",
      isLoading: true,
    }));

    try {
      const response = await evaluatePortfolio(strategy, {
        timestamp,
        price,
        usd_amount: usdAmount,
        asset_amount: assetAmount,
        avg_entry_price: avgEntryPrice,
      });

      setPortfolioState({
        timestamp,
        price,
        usd_amount: usdAmount,
        asset_amount: assetAmount,
        avg_entry_price: avgEntryPrice,
        result: response.portfolio,
        error: "",
        isLoading: false,
      });
    } catch (error) {
      setPortfolioState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Portfolio evaluation failed.",
        isLoading: false,
      }));
    }
  };

  const onModeChange = (nextMode: Mode) => {
    setMode(nextMode);
    const url = new URL(window.location.href);
    if (nextMode === "use") {
      url.searchParams.set("mode", "use");
    } else {
      url.searchParams.delete("mode");
    }
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  };

  return (
    <main className="app-shell">
      <header className="topbar panel">
        <h1>PSA Web</h1>

        <div className="topbar-actions">
          <div className="mode-toggle" role="tablist" aria-label="Screen mode">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "create"}
              className={mode === "create" ? "active" : ""}
              onClick={() => onModeChange("create")}
            >
              Create
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "use"}
              className={mode === "use" ? "active" : ""}
              onClick={() => onModeChange("use")}
            >
              Use
            </button>
            <a className="mode-toggle-link" href="/docs/en">
              Docs
            </a>
          </div>
        </div>
      </header>

      {mode === "create" ? (
        <CreateScreen
          strategy={strategy}
          priceSegmentIds={priceSegmentIds}
          lockedPriceSegmentIdSet={lockedPriceSegmentIdSet}
          priceWeightTotal={priceWeightTotal}
          weightTarget={weightTarget}
          jsonText={jsonText}
          jsonStatus={jsonStatus}
          jsonError={jsonError}
          validationIssues={validationIssues}
          charts={charts}
          chartLoading={chartLoading}
          chartError={chartError}
          chartTimestamp={chartTimestamp}
          onChartTimestampChange={setChartTimestamp}
          onJsonTextChange={(value) => {
            setJsonText(value);
            if (jsonStatus) {
              setJsonStatus("");
            }
            if (jsonError) {
              setJsonError("");
            }
          }}
          onApplyJson={onApplyJson}
          onSaveJson={onSaveJson}
          onUploadJson={(event) => void onUploadJson(event)}
          onMarketModeChange={(marketMode) =>
            updateStrategy((current) => ({
              ...current,
              market_mode: marketMode,
            }))
          }
          onPriceSegmentChange={(index, field, value) =>
            updateStrategy((current) => {
              if (field !== "weight") {
                return {
                  ...current,
                  price_segments: current.price_segments.map((row, rowIndex) =>
                    rowIndex === index
                      ? {
                          ...row,
                          [field]: sanitizeNumber(value),
                        }
                      : row,
                  ),
                };
              }

              const rows = current.price_segments.map((row, rowIndex) => ({
                id: priceSegmentIds[rowIndex] ?? `missing-${rowIndex}`,
                weight: row.weight,
              }));
              const rebalanced = rebalanceWeightsAfterEdit(
                rows,
                rows[index]?.id ?? "",
                sanitizeNumber(value),
                lockedPriceSegmentIds,
              );

              return {
                ...current,
                price_segments: current.price_segments.map((row, rowIndex) => ({
                  ...row,
                  weight: rebalanced[rowIndex]?.weight ?? row.weight,
                })),
              };
            })
          }
          onAddPriceSegment={() =>
            updateStrategy((current) => {
              const currentMin = Math.min(
                ...current.price_segments.map((row) => Math.min(row.price_low, row.price_high)),
              );
              const anchorHigh = Number.isFinite(currentMin) ? currentMin : bounds.max;
              const nextHigh = Math.max(0.02, anchorHigh);
              const nextLow = Math.max(
                0.01,
                Math.min(nextHigh * 0.8, nextHigh - 0.01),
              );

              const nextRows = normalizeWeightsToHundred(
                current.price_segments
                  .map((row, rowIndex) => ({
                    id: priceSegmentIds[rowIndex] ?? `missing-${rowIndex}`,
                    weight: row.weight,
                  }))
                  .concat([{ id: "new-segment", weight: 0 }]),
              );

              const nextSegments = [
                ...current.price_segments,
                {
                  price_low: nextLow,
                  price_high: nextHigh,
                  weight: 0,
                },
              ];

              return {
                ...current,
                price_segments: nextSegments.map((row, rowIndex) => ({
                  ...row,
                  weight: nextRows[rowIndex]?.weight ?? row.weight,
                })),
              };
            })
          }
          onRemovePriceSegment={(index) =>
            (() => {
              const removedId = priceSegmentIds[index];
              setPriceSegmentIds((currentIds) =>
                currentIds.filter((_, rowIndex) => rowIndex !== index),
              );
              setLockedPriceSegmentIds((currentIds) =>
                currentIds.filter((id) => id !== removedId),
              );

              updateStrategy((current) => {
                const rows = current.price_segments.map((row, rowIndex) => ({
                  id: priceSegmentIds[rowIndex] ?? `missing-${rowIndex}`,
                  weight: row.weight,
                }));
                const nextRows = removedId
                  ? rebalanceWeightsAfterRemoval(rows, removedId)
                  : rows.slice(0, -1);

                const nextSegments = current.price_segments
                  .filter((_, rowIndex) => rowIndex !== index)
                  .map((row, rowIndex) => ({
                    ...row,
                    weight: nextRows[rowIndex]?.weight ?? row.weight,
                  }));

                return {
                  ...current,
                  price_segments: nextSegments,
                };
              });
            })()
          }
          onTogglePriceSegmentLock={(segmentId) =>
            setLockedPriceSegmentIds((current) =>
              current.includes(segmentId)
                ? current.filter((id) => id !== segmentId)
                : [...current, segmentId],
            )
          }
          onUnlockAllPriceSegmentLocks={() => setLockedPriceSegmentIds([])}
          onNormalizePriceSegmentWeights={() =>
            updateStrategy((current) => {
              const rows = current.price_segments.map((row, rowIndex) => ({
                id: priceSegmentIds[rowIndex] ?? `missing-${rowIndex}`,
                weight: row.weight,
              }));
              const normalized = normalizeWeightsToHundred(rows);

              return {
                ...current,
                price_segments: current.price_segments.map((row, rowIndex) => ({
                  ...row,
                  weight: normalized[rowIndex]?.weight ?? row.weight,
                })),
              };
            })
          }
          onTimeSegmentChange={(index, field, value) =>
            updateStrategy((current) => ({
              ...current,
              time_segments: current.time_segments.map((row, rowIndex) =>
                rowIndex === index
                  ? {
                      ...row,
                      [field]:
                        typeof value === "number" ? sanitizeNumber(value) : value,
                    }
                  : row,
              ),
            }))
          }
          onAddTimeSegment={() =>
            updateStrategy((current) => {
              const startTs = nowIso();
              const endTs = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
              return {
                ...current,
                time_segments: [
                  ...current.time_segments,
                  {
                    start_ts: startTs,
                    end_ts: endTs,
                    k_start: 1,
                    k_end: 1.2,
                  },
                ],
              };
            })
          }
          onRemoveTimeSegment={(index) =>
            updateStrategy((current) => ({
              ...current,
              time_segments: current.time_segments.filter((_, rowIndex) => rowIndex !== index),
            }))
          }
        />
      ) : (
        <UseScreen
          marketMode={strategy.market_mode}
          nowPoint={nowPoint}
          customPoint={customPoint}
          portfolioState={portfolioState}
          nowPriceInput={nowPriceInput}
          customPriceInput={customPriceInput}
          customTimestampInput={customTimestampInput}
          portfolioTimestampInput={portfolioTimestampInput}
          portfolioPriceInput={portfolioPriceInput}
          portfolioUsdInput={portfolioUsdInput}
          portfolioAssetInput={portfolioAssetInput}
          portfolioAvgEntryPriceInput={portfolioAvgEntryPriceInput}
          validationIssues={validationIssues}
          charts={charts}
          chartLoading={chartLoading}
          chartError={chartError}
          chartTimestamp={chartTimestamp}
          onChartTimestampChange={setChartTimestamp}
          onNowPriceChange={(value) => setNowPriceInput(sanitizePositivePrice(value))}
          onCustomPriceChange={(value) => setCustomPriceInput(sanitizePositivePrice(value))}
          onCustomTimestampChange={(value) => setCustomTimestampInput(value)}
          onPortfolioTimestampChange={setPortfolioTimestampInput}
          onPortfolioPriceChange={(value) => setPortfolioPriceInput(sanitizePositivePrice(value))}
          onPortfolioUsdChange={(value) => setPortfolioUsdInput(sanitizeNonNegativeNumber(value))}
          onPortfolioAssetChange={(value) =>
            setPortfolioAssetInput(sanitizeNonNegativeNumber(value))
          }
          onPortfolioAvgEntryPriceChange={setPortfolioAvgEntryPriceInput}
          onEvaluateNow={() => void evaluateNow()}
          onEvaluateCustom={() => void evaluateCustom()}
          onEvaluatePortfolio={() => void evaluatePortfolioSnapshot()}
        />
      )}
    </main>
  );
}
