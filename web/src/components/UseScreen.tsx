import { ChartDataBundle, UsePointState, UsePortfolioState } from "../lib/types";
import { toLocalDateTimeInput, fromLocalDateTimeInput } from "../lib/strategy";
import { ChartsPanel } from "./ChartsPanel";

type UseScreenProps = {
  marketMode: "bear" | "bull";
  nowPoint: UsePointState;
  customPoint: UsePointState;
  portfolioState: UsePortfolioState;
  nowPriceInput: number;
  customPriceInput: number;
  customTimestampInput: string;
  portfolioTimestampInput: string;
  portfolioPriceInput: number;
  portfolioUsdInput: number;
  portfolioAssetInput: number;
  portfolioAvgEntryPriceInput: string;
  validationIssues: string[];
  charts: ChartDataBundle;
  chartLoading: boolean;
  chartError: string;
  chartTimestamp: string;
  onChartTimestampChange: (timestamp: string) => void;
  onNowPriceChange: (value: number) => void;
  onCustomPriceChange: (value: number) => void;
  onCustomTimestampChange: (value: string) => void;
  onPortfolioTimestampChange: (value: string) => void;
  onPortfolioPriceChange: (value: number) => void;
  onPortfolioUsdChange: (value: number) => void;
  onPortfolioAssetChange: (value: number) => void;
  onPortfolioAvgEntryPriceChange: (value: string) => void;
  onEvaluateNow: () => void;
  onEvaluateCustom: () => void;
  onEvaluatePortfolio: () => void;
};

const formatPercent = (value: number): string => `${(value * 100).toFixed(2)}%`;

const formatPrice = (value: number): string =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

const formatNumber = (value: number, digits = 4): string =>
  new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(value);

const formatNullablePrice = (value: number | null): string =>
  value === null ? "n/a" : formatPrice(value);

const formatNullablePercent = (value: number | null): string =>
  value === null ? "n/a" : formatPercent(value);

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

function PortfolioResultCard({ point }: { point: UsePortfolioState }) {
  return (
    <div className="result-card">
      <h3>Portfolio Result</h3>
      {point.isLoading && <p className="status">Evaluating...</p>}
      {point.error && <p className="status error">{point.error}</p>}
      {point.result && (
        <div className="result-grid">
          <div>date: {formatReadableTimestamp(point.result.timestamp)}</div>
          <div>price: {formatPrice(point.result.price)}</div>
          <div>current share: {formatPercent(point.result.base_share)}</div>
          <div>target share: {formatPercent(point.result.target_share)}</div>
          <div>deviation: {formatPercent(point.result.share_deviation)}</div>
          <div>portfolio value: {formatPrice(point.result.portfolio_value_usd)}</div>
          <div>asset value: {formatPrice(point.result.asset_value_usd)}</div>
          <div>cash value: {formatPrice(point.result.usd_value_usd)}</div>
          <div>target asset amount: {formatNumber(point.result.target_asset_amount)}</div>
          <div>asset amount delta: {formatNumber(point.result.asset_amount_delta)}</div>
          <div>USD delta: {formatPrice(point.result.usd_delta)}</div>
          <div>alignment price: {formatNullablePrice(point.result.alignment_price)}</div>
          <div>avg entry: {formatNullablePrice(point.result.avg_entry_price)}</div>
          <div>avg entry pnl USD: {formatNullablePrice(point.result.avg_entry_pnl_usd)}</div>
          <div>avg entry pnl %: {formatNullablePercent(point.result.avg_entry_pnl_pct)}</div>
        </div>
      )}
    </div>
  );
}

export function UseScreen({
  marketMode,
  nowPoint,
  customPoint,
  portfolioState,
  nowPriceInput,
  customPriceInput,
  customTimestampInput,
  portfolioTimestampInput,
  portfolioPriceInput,
  portfolioUsdInput,
  portfolioAssetInput,
  portfolioAvgEntryPriceInput,
  validationIssues,
  charts,
  chartLoading,
  chartError,
  chartTimestamp,
  onChartTimestampChange,
  onNowPriceChange,
  onCustomPriceChange,
  onCustomTimestampChange,
  onPortfolioTimestampChange,
  onPortfolioPriceChange,
  onPortfolioUsdChange,
  onPortfolioAssetChange,
  onPortfolioAvgEntryPriceChange,
  onEvaluateNow,
  onEvaluateCustom,
  onEvaluatePortfolio,
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

          <div className="use-block">
            <h3>Portfolio</h3>
            <label>
              timestamp
              <input
                type="datetime-local"
                value={toLocalDateTimeInput(portfolioTimestampInput)}
                onChange={(event) =>
                  onPortfolioTimestampChange(fromLocalDateTimeInput(event.target.value))
                }
              />
            </label>
            <label>
              price
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={portfolioPriceInput}
                onChange={(event) => onPortfolioPriceChange(Number(event.target.value))}
              />
            </label>
            <label>
              usd_amount
              <input
                type="number"
                min="0"
                step="0.01"
                value={portfolioUsdInput}
                onChange={(event) => onPortfolioUsdChange(Number(event.target.value))}
              />
            </label>
            <label>
              asset_amount
              <input
                type="number"
                min="0"
                step="0.000001"
                value={portfolioAssetInput}
                onChange={(event) => onPortfolioAssetChange(Number(event.target.value))}
              />
            </label>
            <label>
              avg_entry_price (optional)
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={portfolioAvgEntryPriceInput}
                onChange={(event) => onPortfolioAvgEntryPriceChange(event.target.value)}
              />
            </label>
            <button type="button" onClick={onEvaluatePortfolio} disabled={hasValidationIssues}>
              Evaluate portfolio
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
          <PortfolioResultCard point={portfolioState} />
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
