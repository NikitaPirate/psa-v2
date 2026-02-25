import { DocsLocale } from "./content";

const PROMPT_EN = [
  "You are configuring a PSA strategy for psa-v2.",
  "Return ONLY valid JSON with no markdown/comments and with these exact top-level keys: market_mode, price_segments, optional time_segments.",
  "Do not add extra keys.",
  "Constraints: market_mode is bear or bull; price_segments has at least one segment and at least one weight > 0; each segment has price_low > 0, price_high > 0, price_low < price_high, weight >= 0; if time_segments is present each row has start_ts and end_ts as ISO-8601 date-time with timezone, start_ts < end_ts, k_start > 0, k_end > 0.",
  "Output JSON shape: { market_mode, price_segments: [{ price_low, price_high, weight }], time_segments?: [{ start_ts, end_ts, k_start, k_end }] }.",
].join(" ");

const PROMPT_RU = [
  "Ты настраиваешь PSA-стратегию для psa-v2.",
  "Верни ТОЛЬКО валидный JSON без markdown/комментариев и с точными top-level ключами: market_mode, price_segments, optional time_segments.",
  "Не добавляй лишние ключи.",
  "Ограничения: market_mode только bear или bull; в price_segments минимум один сегмент и минимум один weight > 0; каждый сегмент содержит price_low > 0, price_high > 0, price_low < price_high, weight >= 0; если есть time_segments, каждая строка содержит start_ts и end_ts в ISO-8601 date-time с timezone, start_ts < end_ts, k_start > 0, k_end > 0.",
  "Форма JSON: { market_mode, price_segments: [{ price_low, price_high, weight }], time_segments?: [{ start_ts, end_ts, k_start, k_end }] }.",
].join(" ");

export function docsPromptByLocale(locale: DocsLocale): string {
  return locale === "ru" ? PROMPT_RU : PROMPT_EN;
}
