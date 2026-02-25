import { ChartDataBundle, UsePointState } from "../lib/types";
import { toLocalDateTimeInput, fromLocalDateTimeInput } from "../lib/strategy";
import { ChartsPanel } from "./ChartsPanel";

type UseScreenProps = {
  marketMode: "bear" | "bull";
  nowPoint: UsePointState;
  customPoint: UsePointState;
  nowPriceInput: number;
  customPriceInput: number;
  customTimestampInput: string;
  validationIssues: string[];
  charts: ChartDataBundle;
  chartLoading: boolean;
  chartError: string;
  chartTimestamp: string;
  onChartTimestampChange: (timestamp: string) => void;
  onNowPriceChange: (value: number) => void;
  onCustomPriceChange: (value: number) => void;
  onCustomTimestampChange: (value: string) => void;
  onEvaluateNow: () => void;
  onEvaluateCustom: () => void;
};

const formatPercent = (value: number): string => `${(value * 100).toFixed(2)}%`;

const formatPrice = (value: number): string =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

const formatReadableTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(date);
};

function ResultCard({ title, point }: { title: string; point: UsePointState }) {
  return (
    <div className="result-card">
      <h3>{title}</h3>
      {point.isLoading && <p className="status">Evaluating...</p>}
      {point.error && <p className="status error">{point.error}</p>}
      {point.result && (
        <div className="result-grid">
          <div>date: {formatReadableTimestamp(point.result.timestamp)}</div>
          <div>price: {formatPrice(point.result.price)}</div>
          <div>share: {formatPercent(point.result.base_share)}</div>
          <div>
            share with time modifier: {formatPercent(point.result.target_share)}
          </div>
          <div>time modifier: {point.result.time_k.toFixed(3)}</div>
        </div>
      )}
    </div>
  );
}

export function UseScreen({
  marketMode,
  nowPoint,
  customPoint,
  nowPriceInput,
  customPriceInput,
  customTimestampInput,
  validationIssues,
  charts,
  chartLoading,
  chartError,
  chartTimestamp,
  onChartTimestampChange,
  onNowPriceChange,
  onCustomPriceChange,
  onCustomTimestampChange,
  onEvaluateNow,
  onEvaluateCustom,
}: UseScreenProps) {
  const hasValidationIssues = validationIssues.length > 0;

  return (
    <>
      <section className="panel">
        <h2>Use</h2>

        <div className="use-controls">
          <div className="use-block">
            <h3>Now</h3>
            <label>
              price
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={nowPriceInput}
                onChange={(event) => onNowPriceChange(Number(event.target.value))}
              />
            </label>
            <button type="button" onClick={onEvaluateNow} disabled={hasValidationIssues}>
              Evaluate now
            </button>
          </div>

          <div className="use-block">
            <h3>Custom Point</h3>
            <label>
              timestamp
              <input
                type="datetime-local"
                value={toLocalDateTimeInput(customTimestampInput)}
                onChange={(event) =>
                  onCustomTimestampChange(fromLocalDateTimeInput(event.target.value))
                }
              />
            </label>
            <label>
              price
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={customPriceInput}
                onChange={(event) => onCustomPriceChange(Number(event.target.value))}
              />
            </label>
            <button type="button" onClick={onEvaluateCustom} disabled={hasValidationIssues}>
              Evaluate point
            </button>
          </div>
        </div>

        {hasValidationIssues && (
          <div className="status error">
            {validationIssues.map((issue) => (
              <p key={issue}>{issue}</p>
            ))}
          </div>
        )}

        <div className="use-results">
          <ResultCard title="Now Result" point={nowPoint} />
          <ResultCard title="Custom Result" point={customPoint} />
        </div>
      </section>

      <ChartsPanel
        marketMode={marketMode}
        charts={charts}
        isLoading={chartLoading}
        error={chartError}
        chartTimestamp={chartTimestamp}
        onChartTimestampChange={onChartTimestampChange}
      />
    </>
  );
}
