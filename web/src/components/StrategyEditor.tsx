import { ChangeEvent } from "react";
import {
  CanonicalPriceSegment,
  CanonicalStrategy,
  CanonicalTimeSegment,
} from "../lib/types";
import { fromLocalDateTimeInput, toLocalDateTimeInput } from "../lib/strategy";

type StrategyEditorProps = {
  strategy: CanonicalStrategy;
  priceSegmentIds: string[];
  lockedPriceSegmentIdSet: Set<string>;
  priceWeightTotal: number;
  weightTarget: number;
  jsonText: string;
  jsonStatus: string;
  jsonError: string;
  validationIssues: string[];
  onJsonTextChange: (text: string) => void;
  onApplyJson: () => void;
  onSaveJson: () => void;
  onUploadJson: (event: ChangeEvent<HTMLInputElement>) => void;
  onMarketModeChange: (mode: CanonicalStrategy["market_mode"]) => void;
  onPriceSegmentChange: (
    index: number,
    field: keyof CanonicalPriceSegment,
    value: number,
  ) => void;
  onAddPriceSegment: () => void;
  onRemovePriceSegment: (index: number) => void;
  onTogglePriceSegmentLock: (segmentId: string) => void;
  onUnlockAllPriceSegmentLocks: () => void;
  onNormalizePriceSegmentWeights: () => void;
  onTimeSegmentChange: (
    index: number,
    field: keyof CanonicalTimeSegment,
    value: string | number,
  ) => void;
  onAddTimeSegment: () => void;
  onRemoveTimeSegment: (index: number) => void;
};

export function StrategyEditor({
  strategy,
  priceSegmentIds,
  lockedPriceSegmentIdSet,
  priceWeightTotal,
  weightTarget,
  jsonText,
  jsonStatus,
  jsonError,
  validationIssues,
  onJsonTextChange,
  onApplyJson,
  onSaveJson,
  onUploadJson,
  onMarketModeChange,
  onPriceSegmentChange,
  onAddPriceSegment,
  onRemovePriceSegment,
  onTogglePriceSegmentLock,
  onUnlockAllPriceSegmentLocks,
  onNormalizePriceSegmentWeights,
  onTimeSegmentChange,
  onAddTimeSegment,
  onRemoveTimeSegment,
}: StrategyEditorProps) {
  return (
    <section className="panel">
      <h2>Create</h2>

      <label htmlFor="strategy-json" className="field-label">
        Strategy JSON
      </label>
      <textarea
        id="strategy-json"
        value={jsonText}
        onChange={(event) => onJsonTextChange(event.target.value)}
      />
      <div className="row-actions">
        <button type="button" onClick={onApplyJson}>
          Apply JSON
        </button>
        <button type="button" onClick={onSaveJson}>
          Save .json
        </button>
        <label className="button-label" htmlFor="upload-json">
          Load .json
          <input
            id="upload-json"
            type="file"
            accept=".json,application/json"
            onChange={onUploadJson}
          />
        </label>
      </div>
      {jsonStatus && <p className="status">{jsonStatus}</p>}
      {jsonError && <p className="status error">{jsonError}</p>}

      <div className="editor-section">
        <label>
          market_mode
          <select
            value={strategy.market_mode}
            onChange={(event) =>
              onMarketModeChange(event.target.value as CanonicalStrategy["market_mode"])
            }
          >
            <option value="bear">bear</option>
            <option value="bull">bull</option>
          </select>
        </label>
      </div>

      <div className="editor-section">
        <div className="section-head">
          <h3>price_segments</h3>
          <div className="row-actions">
            <button type="button" onClick={onNormalizePriceSegmentWeights}>
              Rebalance to 100
            </button>
            <button type="button" onClick={onUnlockAllPriceSegmentLocks}>
              Unlock weights
            </button>
            <button type="button" onClick={onAddPriceSegment}>
              Add row
            </button>
          </div>
        </div>

        <div className="weight-overview" role="status" aria-live="polite">
          <div className="weight-overview-head">
            <span>Allocated weight</span>
            <strong>{`${priceWeightTotal.toFixed(2)} / ${weightTarget.toFixed(2)}`}</strong>
          </div>
          <div className="weight-stacked-bar" aria-hidden="true">
            {strategy.price_segments.map((row, index) => (
              <span
                key={`weight-${priceSegmentIds[index] ?? index}`}
                className="weight-stacked-piece"
                style={{ width: `${Math.max(0, Math.min(100, row.weight))}%` }}
              />
            ))}
          </div>
        </div>

        {strategy.price_segments.map((row, index) => {
          const segmentId = priceSegmentIds[index] ?? `missing-${index}`;
          return (
          <div className="segment-row" key={`price-${segmentId}`}>
            <label>
              price_low
              <input
                type="number"
                min="0"
                step="1"
                value={row.price_low}
                onChange={(event) =>
                  onPriceSegmentChange(index, "price_low", Number(event.target.value))
                }
              />
            </label>
            <label>
              price_high
              <input
                type="number"
                min="0"
                step="1"
                value={row.price_high}
                onChange={(event) =>
                  onPriceSegmentChange(index, "price_high", Number(event.target.value))
                }
              />
            </label>
            <label>
              weight
              <input
                type="number"
                min="0"
                max={weightTarget}
                step="0.01"
                value={row.weight}
                disabled={lockedPriceSegmentIdSet.has(segmentId)}
                onChange={(event) =>
                  onPriceSegmentChange(index, "weight", Number(event.target.value))
                }
              />
            </label>
            <label className="weight-slider">
              weight slider
              <input
                type="range"
                min="0"
                max={weightTarget}
                step="0.01"
                value={row.weight}
                disabled={lockedPriceSegmentIdSet.has(segmentId)}
                onChange={(event) =>
                  onPriceSegmentChange(index, "weight", Number(event.target.value))
                }
              />
            </label>
            <label className="weight-lock">
              <input
                type="checkbox"
                checked={lockedPriceSegmentIdSet.has(segmentId)}
                onChange={() => onTogglePriceSegmentLock(segmentId)}
              />
              Lock weight
            </label>
            <button
              type="button"
              className="danger"
              onClick={() => onRemovePriceSegment(index)}
              disabled={strategy.price_segments.length <= 1}
            >
              Remove
            </button>
          </div>
          );
        })}
      </div>

      <div className="editor-section">
        <div className="section-head">
          <h3>time_segments</h3>
          <button type="button" onClick={onAddTimeSegment}>
            Add row
          </button>
        </div>

        {strategy.time_segments.length === 0 ? (
          <p className="status muted">No time segments</p>
        ) : (
          strategy.time_segments.map((row, index) => (
            <div className="segment-row time" key={`time-${index}`}>
              <label>
                start_ts
                <input
                  type="datetime-local"
                  value={toLocalDateTimeInput(row.start_ts)}
                  onChange={(event) =>
                    onTimeSegmentChange(
                      index,
                      "start_ts",
                      fromLocalDateTimeInput(event.target.value),
                    )
                  }
                />
              </label>
              <label>
                end_ts
                <input
                  type="datetime-local"
                  value={toLocalDateTimeInput(row.end_ts)}
                  onChange={(event) =>
                    onTimeSegmentChange(
                      index,
                      "end_ts",
                      fromLocalDateTimeInput(event.target.value),
                    )
                  }
                />
              </label>
              <label>
                k_start
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={row.k_start}
                  onChange={(event) =>
                    onTimeSegmentChange(index, "k_start", Number(event.target.value))
                  }
                />
              </label>
              <label>
                k_end
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={row.k_end}
                  onChange={(event) =>
                    onTimeSegmentChange(index, "k_end", Number(event.target.value))
                  }
                />
              </label>
              <button
                type="button"
                className="danger"
                onClick={() => onRemoveTimeSegment(index)}
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>

      {validationIssues.length > 0 && (
        <div className="status error">
          {validationIssues.map((issue) => (
            <p key={issue}>{issue}</p>
          ))}
        </div>
      )}
    </section>
  );
}
