import { CanonicalStrategy } from "../lib/types";

export type DocsLocale = "en" | "ru";

type LocalizedValue<T> = Record<DocsLocale, T>;

type ContextForHuman = {
  intro: LocalizedValue<string>;
  assumptionsLabel: LocalizedValue<string>;
  assumptions: LocalizedValue<string[]>;
  disclaimer: LocalizedValue<string>;
  strategyDefinition: LocalizedValue<string>;
  configurableLabel: LocalizedValue<string>;
  configurableItems: LocalizedValue<string[]>;
  outputPolicy: LocalizedValue<string>;
};

export const CONTEXT_FOR_HUMAN_VERBATIM: ContextForHuman = {
  intro: {
    en: "This strategy comes from my personal assumptions about the BTC market. I use it as a disciplined way to build a position within my cycle hypothesis.",
    ru: "Эта стратегия появилась из моих личных предпосылок о рынке BTC. Я использую её как способ дисциплинированно собирать позицию в рамках своей гипотезы о циклах.",
  },
  assumptionsLabel: {
    en: "My current assumptions:",
    ru: "Мои текущие допущения:",
  },
  assumptions: {
    en: [
      "BTC cyclicality remains in place, and the current phase resembles a crypto winter.",
      "I expect the weak phase to end roughly by October of this year.",
      "I consider a sub-$25k scenario unlikely.",
    ],
    ru: [
      "цикличность BTC сохраняется, и текущая фаза похожа на «криптозиму»;",
      "окончание фазы слабости я ожидаю ориентировочно к октябрю текущего года;",
      "сценарий ниже $25k я считаю маловероятным.",
    ],
  },
  disclaimer: {
    en: "These are subjective expectations, not assertions. PSA does not attempt to predict price and is not investment advice.",
    ru: "Это субъективные ожидания, а не утверждения. PSA не пытается предсказать цену и не является инвестиционной рекомендацией.",
  },
  strategyDefinition: {
    en: "PSA is a price/time guideline for building a position: a rule that maps current conditions (price) and time (date) to a target BTC share in a portfolio.",
    ru: "PSA - это прайс/тайм-ориентир для набора позиции: правило, которое сопоставляет текущим условиям (цене) и времени (дате) целевую долю BTC в портфеле.",
  },
  configurableLabel: {
    en: "The strategy is fully user-configurable:",
    ru: "Стратегия полностью настраивается пользователем:",
  },
  configurableItems: {
    en: [
      "price mapping (segments/ranges and target shares for them);",
      "time logic (a modifier that increases the target share as the chosen horizon approaches).",
    ],
    ru: [
      "ценовой разметкой (сегменты/диапазоны и целевые доли для них);",
      "временной логикой (модификатор, который усиливает целевую долю по мере приближения к выбранному горизонту).",
    ],
  },
  outputPolicy: {
    en: "PSA output is not a signal but a guideline: it shows a target BTC share, while the decision whether to buy and how often remains with the user.",
    ru: "Результат PSA - не сигнал, а ориентир: стратегия показывает целевую долю BTC, а решение о том, покупать ли и как часто, остаётся на стороне пользователя.",
  },
};

export const DOCS_JSON_EXAMPLE: CanonicalStrategy = {
  market_mode: "bear",
  price_segments: [
    { price_low: 55000, price_high: 70000, weight: 15 },
    { price_low: 42000, price_high: 55000, weight: 35 },
    { price_low: 28000, price_high: 42000, weight: 45 },
    { price_low: 25000, price_high: 28000, weight: 5 },
  ],
  time_segments: [
    {
      start_ts: "2026-03-01T00:00:00Z",
      end_ts: "2026-10-01T00:00:00Z",
      k_start: 1,
      k_end: 1.7,
    },
  ],
};

export const DOCS_TEXT = {
  title: {
    en: "PSA v2 Documentation",
    ru: "Документация PSA v2",
  },
  createTab: {
    en: "Create",
    ru: "Create",
  },
  useTab: {
    en: "Use",
    ru: "Use",
  },
  docsTab: {
    en: "Docs",
    ru: "Docs",
  },
  language: {
    en: "Language",
    ru: "Язык",
  },
  tocTitle: {
    en: "Contents",
    ru: "Содержание",
  },
  contextTitle: {
    en: "Context for Human",
    ru: "Context for Human",
  },
  promptTitle: {
    en: "Prompt for AI Assistant",
    ru: "Prompt for AI Assistant",
  },
  promptLine: {
    en: "Use one copy-ready prompt that matches current psa-v2 schema and agent-first workflow.",
    ru: "Используйте один готовый для копирования промпт под актуальную схему psa-v2 и agent-first workflow.",
  },
  copyPrompt: {
    en: "Copy prompt",
    ru: "Скопировать промпт",
  },
  promptCopied: {
    en: "Prompt copied.",
    ru: "Промпт скопирован.",
  },
  promptCopyError: {
    en: "Unable to copy prompt in this browser.",
    ru: "Не удалось скопировать промпт в этом браузере.",
  },
  chartsTitle: {
    en: "How to Read Charts",
    ru: "How to Read Charts",
  },
  chartsItems: {
    en: [
      "Chart 1 (Price vs Share): shows base share without time modifier; axis direction depends on market_mode.",
      "Chart 2 (Heatmap): date x price map of target share; available when time_segments are present and include future range.",
      "Chart 3 (3D Surface): same target-share surface in 3D for trend visibility across date and price.",
    ],
    ru: [
      "Chart 1 (Price vs Share): показывает базовую долю без time modifier; направление оси зависит от market_mode.",
      "Chart 2 (Heatmap): карта target share по осям date x price; доступна, когда есть time_segments с будущим диапазоном.",
      "Chart 3 (3D Surface): та же поверхность target share в 3D для наглядности тренда по дате и цене.",
    ],
  },
  configureTitle: {
    en: "Configure Strategy (Web or Agent)",
    ru: "Configure Strategy (Web or Agent)",
  },
  configureIntro: {
    en: "Create is available through two equivalent paths: Web UI and Agent+CLI. Choose by workflow, not by data model.",
    ru: "Create доступен двумя равноправными путями: через Web UI и через Agent+CLI. Выбор зависит от workflow, а не от модели данных.",
  },
  configureItems: {
    en: [
      "Web path: use Create for canonical JSON editing and chart checks, then Use for point/scenario evaluation.",
      "Agent path: install runtime (uv tool install psa-strategy-cli), install skill (psa install-skill codex --json), then work through psa strategy/log/evaluate commands.",
      "Both paths rely on the same canonical strategy payload and the same core semantics.",
      "Switch paths freely: draft in one surface, validate or continue in another.",
    ],
    ru: [
      "Web-путь: используйте Create для редактирования canonical JSON и проверки графиков, затем Use для point/scenario evaluation.",
      "Agent-путь: установите runtime (uv tool install psa-strategy-cli), установите skill (psa install-skill codex --json), затем работайте через psa strategy/log/evaluate команды.",
      "Оба пути используют один и тот же canonical strategy payload и одинаковую семантику core.",
      "Пути можно свободно сочетать: черновик в одном интерфейсе, проверка и продолжение - в другом.",
    ],
  },
  jsonTitle: {
    en: "JSON Workflow and Schema",
    ru: "JSON Workflow and Schema",
  },
  jsonIntro: {
    en: "Canonical transferable payload is owned by schemas/strategy_upsert.request.v1.json.",
    ru: "Канонический переносимый payload определяется в schemas/strategy_upsert.request.v1.json.",
  },
  jsonConstraintsTitle: {
    en: "Current constraints",
    ru: "Текущие ограничения",
  },
  jsonConstraints: {
    en: [
      "market_mode: bear | bull",
      "price_segments: required, min 1 item, at least one segment with weight > 0",
      "time_segments: optional; if present, use ISO-8601 date-time with timezone and k_start/k_end > 0",
      "No extra keys in strategy object or segment objects (additionalProperties: false)",
    ],
    ru: [
      "market_mode: bear | bull",
      "price_segments: обязательно, минимум 1 элемент, минимум один сегмент с weight > 0",
      "time_segments: опционально; при наличии используйте ISO-8601 date-time с timezone и k_start/k_end > 0",
      "Без лишних ключей в объекте стратегии и сегментах (additionalProperties: false)",
    ],
  },
  jsonTransferTitle: {
    en: "Transfer notes",
    ru: "Transfer notes",
  },
  jsonTransferItems: {
    en: [
      "Raw JSON text and .json file content are equivalent representations of the same payload.",
      "psa strategy show --json returns metadata wrapper; use nested strategy field as canonical transferable body.",
    ],
    ru: [
      "Raw JSON текст и .json-файл эквивалентны как представления одного payload.",
      "psa strategy show --json возвращает обертку с метаданными; для переноса используйте вложенное поле strategy.",
    ],
  },
} as const;
