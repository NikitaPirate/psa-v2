import { ChangeEvent } from "react";
import {
  CanonicalPriceSegment,
  CanonicalStrategy,
  CanonicalTimeSegment,
  ChartDataBundle,
} from "../lib/types";
import { StrategyEditor } from "./StrategyEditor";
import { ChartsPanel } from "./ChartsPanel";

type CreateScreenProps = {
  strategy: CanonicalStrategy;
  priceSegmentIds: string[];
  lockedPriceSegmentIdSet: Set<string>;
  priceWeightTotal: number;
  weightTarget: number;
  jsonText: string;
  jsonStatus: string;
  jsonError: string;
  validationIssues: string[];
  charts: ChartDataBundle;
  chartLoading: boolean;
  chartError: string;
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

export function CreateScreen(props: CreateScreenProps) {
  return (
    <>
      <StrategyEditor
        strategy={props.strategy}
        priceSegmentIds={props.priceSegmentIds}
        lockedPriceSegmentIdSet={props.lockedPriceSegmentIdSet}
        priceWeightTotal={props.priceWeightTotal}
        weightTarget={props.weightTarget}
        jsonText={props.jsonText}
        jsonStatus={props.jsonStatus}
        jsonError={props.jsonError}
        validationIssues={props.validationIssues}
        onJsonTextChange={props.onJsonTextChange}
        onApplyJson={props.onApplyJson}
        onSaveJson={props.onSaveJson}
        onUploadJson={props.onUploadJson}
        onMarketModeChange={props.onMarketModeChange}
        onPriceSegmentChange={props.onPriceSegmentChange}
        onAddPriceSegment={props.onAddPriceSegment}
        onRemovePriceSegment={props.onRemovePriceSegment}
        onTogglePriceSegmentLock={props.onTogglePriceSegmentLock}
        onUnlockAllPriceSegmentLocks={props.onUnlockAllPriceSegmentLocks}
        onNormalizePriceSegmentWeights={props.onNormalizePriceSegmentWeights}
        onTimeSegmentChange={props.onTimeSegmentChange}
        onAddTimeSegment={props.onAddTimeSegment}
        onRemoveTimeSegment={props.onRemoveTimeSegment}
      />
      <ChartsPanel
        marketMode={props.strategy.market_mode}
        charts={props.charts}
        isLoading={props.chartLoading}
        error={props.chartError}
      />
    </>
  );
}
