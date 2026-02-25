import { describe, expect, it } from "vitest";
import { parseCanonicalStrategy } from "./strategy";

const validBase = {
  market_mode: "bear",
  price_segments: [{ price_low: 10000, price_high: 20000, weight: 100 }],
};

describe("parseCanonicalStrategy timezone validation", () => {
  it("accepts time segments with explicit timezone", () => {
    const parsed = parseCanonicalStrategy(
      JSON.stringify({
        ...validBase,
        time_segments: [
          {
            start_ts: "2026-01-01T00:00:00Z",
            end_ts: "2026-02-01T00:00:00+00:00",
            k_start: 1,
            k_end: 1.2,
          },
        ],
      }),
    );

    expect(parsed.time_segments).toHaveLength(1);
  });

  it("rejects time segments without timezone", () => {
    expect(() =>
      parseCanonicalStrategy(
        JSON.stringify({
          ...validBase,
          time_segments: [
            {
              start_ts: "2026-01-01T00:00:00",
              end_ts: "2026-02-01T00:00:00Z",
              k_start: 1,
              k_end: 1.2,
            },
          ],
        }),
      ),
    ).toThrowError(/start_ts must be ISO with timezone/i);
  });
});
