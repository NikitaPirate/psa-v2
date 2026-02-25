import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { parseCanonicalStrategy } from "../lib/strategy";
import { CONTEXT_FOR_HUMAN_VERBATIM, DOCS_JSON_EXAMPLE } from "./content";
import { DocsPage } from "./DocsPage";

const EXPECTED_CONTEXT_EN = {
  intro:
    "This strategy comes from my personal assumptions about the BTC market. I use it as a disciplined way to build a position within my cycle hypothesis.",
  assumptions: [
    "BTC cyclicality remains in place, and the current phase resembles a crypto winter.",
    "I expect the weak phase to end roughly by October of this year.",
    "I consider a sub-$25k scenario unlikely.",
  ],
  disclaimer:
    "These are subjective expectations, not assertions. PSA does not attempt to predict price and is not investment advice.",
  strategyDefinition:
    "PSA is a price/time guideline for building a position: a rule that maps current conditions (price) and time (date) to a target BTC share in a portfolio.",
  configurableItems: [
    "price mapping (segments/ranges and target shares for them);",
    "time logic (a modifier that increases the target share as the chosen horizon approaches).",
  ],
  outputPolicy:
    "PSA output is not a signal but a guideline: it shows a target BTC share, while the decision whether to buy and how often remains with the user.",
};

const EXPECTED_CONTEXT_RU = {
  intro:
    "Эта стратегия появилась из моих личных предпосылок о рынке BTC. Я использую её как способ дисциплинированно собирать позицию в рамках своей гипотезы о циклах.",
  assumptions: [
    "цикличность BTC сохраняется, и текущая фаза похожа на «криптозиму»;",
    "окончание фазы слабости я ожидаю ориентировочно к октябрю текущего года;",
    "сценарий ниже $25k я считаю маловероятным.",
  ],
  disclaimer:
    "Это субъективные ожидания, а не утверждения. PSA не пытается предсказать цену и не является инвестиционной рекомендацией.",
  strategyDefinition:
    "PSA - это прайс/тайм-ориентир для набора позиции: правило, которое сопоставляет текущим условиям (цене) и времени (дате) целевую долю BTC в портфеле.",
  configurableItems: [
    "ценовой разметкой (сегменты/диапазоны и целевые доли для них);",
    "временной логикой (модификатор, который усиливает целевую долю по мере приближения к выбранному горизонту).",
  ],
  outputPolicy:
    "Результат PSA - не сигнал, а ориентир: стратегия показывает целевую долю BTC, а решение о том, покупать ли и как часто, остаётся на стороне пользователя.",
};

describe("docs content", () => {
  it("keeps Context for Human EN/RU text verbatim", () => {
    expect(CONTEXT_FOR_HUMAN_VERBATIM.intro.en).toBe(EXPECTED_CONTEXT_EN.intro);
    expect(CONTEXT_FOR_HUMAN_VERBATIM.assumptions.en).toEqual(EXPECTED_CONTEXT_EN.assumptions);
    expect(CONTEXT_FOR_HUMAN_VERBATIM.disclaimer.en).toBe(EXPECTED_CONTEXT_EN.disclaimer);
    expect(CONTEXT_FOR_HUMAN_VERBATIM.strategyDefinition.en).toBe(
      EXPECTED_CONTEXT_EN.strategyDefinition,
    );
    expect(CONTEXT_FOR_HUMAN_VERBATIM.configurableItems.en).toEqual(
      EXPECTED_CONTEXT_EN.configurableItems,
    );
    expect(CONTEXT_FOR_HUMAN_VERBATIM.outputPolicy.en).toBe(EXPECTED_CONTEXT_EN.outputPolicy);

    expect(CONTEXT_FOR_HUMAN_VERBATIM.intro.ru).toBe(EXPECTED_CONTEXT_RU.intro);
    expect(CONTEXT_FOR_HUMAN_VERBATIM.assumptions.ru).toEqual(EXPECTED_CONTEXT_RU.assumptions);
    expect(CONTEXT_FOR_HUMAN_VERBATIM.disclaimer.ru).toBe(EXPECTED_CONTEXT_RU.disclaimer);
    expect(CONTEXT_FOR_HUMAN_VERBATIM.strategyDefinition.ru).toBe(
      EXPECTED_CONTEXT_RU.strategyDefinition,
    );
    expect(CONTEXT_FOR_HUMAN_VERBATIM.configurableItems.ru).toEqual(
      EXPECTED_CONTEXT_RU.configurableItems,
    );
    expect(CONTEXT_FOR_HUMAN_VERBATIM.outputPolicy.ru).toBe(EXPECTED_CONTEXT_RU.outputPolicy);
  });

  it("shows How to Read Charts section with all chart types", () => {
    render(
      <DocsPage
        locale="en"
        onNavigateToApp={() => {
          return;
        }}
        onLocaleChange={() => {
          return;
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "How to Read Charts" })).toBeInTheDocument();
    expect(screen.getByText(/Chart 1 \(Price vs Share\)/)).toBeInTheDocument();
    expect(screen.getByText(/Chart 2 \(Heatmap\)/)).toBeInTheDocument();
    expect(screen.getByText(/Chart 3 \(3D Surface\)/)).toBeInTheDocument();
    expect(screen.getByText(/available when time_segments are present/i)).toBeInTheDocument();
  });

  it("keeps canonical JSON example aligned with current schema constraints", () => {
    expect(Object.keys(DOCS_JSON_EXAMPLE).sort()).toEqual([
      "market_mode",
      "price_segments",
      "time_segments",
    ]);

    expect(["bear", "bull"]).toContain(DOCS_JSON_EXAMPLE.market_mode);
    expect(DOCS_JSON_EXAMPLE.price_segments.length).toBeGreaterThan(0);
    expect(DOCS_JSON_EXAMPLE.price_segments.some((segment) => segment.weight > 0)).toBe(true);

    DOCS_JSON_EXAMPLE.price_segments.forEach((segment) => {
      expect(Object.keys(segment).sort()).toEqual(["price_high", "price_low", "weight"]);
      expect(segment.price_low).toBeGreaterThan(0);
      expect(segment.price_high).toBeGreaterThan(0);
      expect(segment.price_low).toBeLessThan(segment.price_high);
      expect(segment.weight).toBeGreaterThanOrEqual(0);
    });

    DOCS_JSON_EXAMPLE.time_segments.forEach((segment) => {
      expect(Object.keys(segment).sort()).toEqual(["end_ts", "k_end", "k_start", "start_ts"]);
      expect(segment.k_start).toBeGreaterThan(0);
      expect(segment.k_end).toBeGreaterThan(0);
      expect(/(Z|[+-]\d{2}:\d{2})$/.test(segment.start_ts)).toBe(true);
      expect(/(Z|[+-]\d{2}:\d{2})$/.test(segment.end_ts)).toBe(true);
    });

    expect(() => parseCanonicalStrategy(JSON.stringify(DOCS_JSON_EXAMPLE))).not.toThrow();
  });
});
