const WEIGHT_TOTAL = 100;
const SCALE = 100;
const TOTAL_UNITS = WEIGHT_TOTAL * SCALE;

export type WeightedRow = {
  id: string;
  weight: number;
};

type WeightedItem<T extends WeightedRow> = {
  row: T;
  index: number;
  baseUnits: number;
  remainder: number;
};

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

const safeWeight = (value: number): number =>
  Number.isFinite(value) ? Math.max(0, value) : 0;

const weightToUnits = (value: number): number => {
  const sanitized = clamp(safeWeight(value), 0, WEIGHT_TOTAL);
  return Math.round(sanitized * SCALE);
};

const unitsToWeight = (units: number): number => units / SCALE;

const allocateByWeights = <T extends WeightedRow>(
  rows: T[],
  targetUnits: number,
  weightSelector: (row: T) => number,
): Map<string, number> => {
  const allocation = new Map<string, number>();

  if (rows.length === 0 || targetUnits <= 0) {
    rows.forEach((row) => allocation.set(row.id, 0));
    return allocation;
  }

  const weighted = rows.map<WeightedItem<T>>((row, index) => {
    const rawWeight = Math.max(0, weightSelector(row));
    return {
      row,
      index,
      baseUnits: 0,
      remainder: rawWeight,
    };
  });

  const totalWeight = weighted.reduce((acc, item) => acc + item.remainder, 0);

  if (totalWeight <= 0) {
    weighted.forEach((item) => allocation.set(item.row.id, 0));
    allocation.set(weighted[0].row.id, targetUnits);
    return allocation;
  }

  weighted.forEach((item) => {
    const exactUnits = (targetUnits * item.remainder) / totalWeight;
    item.baseUnits = Math.floor(exactUnits);
    item.remainder = exactUnits - item.baseUnits;
  });

  let assignedUnits = weighted.reduce((acc, item) => acc + item.baseUnits, 0);
  const sortedByRemainder = [...weighted].sort((left, right) => {
    if (right.remainder !== left.remainder) {
      return right.remainder - left.remainder;
    }
    return left.index - right.index;
  });

  for (let idx = 0; assignedUnits < targetUnits; idx += 1, assignedUnits += 1) {
    const item = sortedByRemainder[idx % sortedByRemainder.length];
    item.baseUnits += 1;
  }

  weighted.forEach((item) => allocation.set(item.row.id, item.baseUnits));
  return allocation;
};

export const sumWeights = (rows: WeightedRow[]): number => {
  const units = rows.reduce((acc, row) => acc + weightToUnits(row.weight), 0);
  return unitsToWeight(units);
};

export const normalizeWeightsToHundred = <T extends WeightedRow>(rows: T[]): T[] => {
  if (rows.length === 0) {
    return [];
  }

  const allocation = allocateByWeights(rows, TOTAL_UNITS, (row) => safeWeight(row.weight));

  return rows.map((row) => ({
    ...row,
    weight: unitsToWeight(allocation.get(row.id) ?? 0),
  }));
};

export const rebalanceWeightsAfterEdit = <T extends WeightedRow>(
  rows: T[],
  editedRowId: string,
  nextWeight: number,
  lockedRowIds: string[] = [],
): T[] => {
  if (rows.length === 0) {
    return [];
  }

  const normalizedRows = normalizeWeightsToHundred(rows);
  if (!normalizedRows.some((row) => row.id === editedRowId)) {
    return normalizedRows;
  }

  const lockedSet = new Set(lockedRowIds);
  lockedSet.delete(editedRowId);

  const fixedRows = normalizedRows.filter((row) => lockedSet.has(row.id));
  const fixedUnits = fixedRows.reduce((acc, row) => acc + weightToUnits(row.weight), 0);

  const adjustedFixedUnits = clamp(fixedUnits, 0, TOTAL_UNITS);
  const maxEditableUnits = Math.max(0, TOTAL_UNITS - adjustedFixedUnits);
  const editedUnits = clamp(weightToUnits(nextWeight), 0, maxEditableUnits);

  const adjustableRows = normalizedRows.filter(
    (row) => row.id !== editedRowId && !lockedSet.has(row.id),
  );
  const remainingUnits = Math.max(0, TOTAL_UNITS - adjustedFixedUnits - editedUnits);
  const adjustableAllocation = allocateByWeights(
    adjustableRows,
    remainingUnits,
    (row) => weightToUnits(row.weight),
  );

  return normalizedRows.map((row) => {
    if (row.id === editedRowId) {
      return {
        ...row,
        weight: unitsToWeight(editedUnits),
      };
    }

    if (lockedSet.has(row.id)) {
      return row;
    }

    return {
      ...row,
      weight: unitsToWeight(adjustableAllocation.get(row.id) ?? 0),
    };
  });
};

export const rebalanceWeightsAfterRemoval = <T extends WeightedRow>(
  rows: T[],
  removedRowId: string,
): T[] => normalizeWeightsToHundred(rows.filter((row) => row.id !== removedRowId));

export const weightTotalTarget = (): number => WEIGHT_TOTAL;
