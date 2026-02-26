import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import {
  PERSISTED_WEB_STATE_STORAGE_KEY,
  PERSISTED_WEB_STATE_VERSION,
  PersistedWebStateV1,
} from "./lib/persistence";
import { toLocalDateTimeInput } from "./lib/strategy";

vi.mock("plotly.js-dist-min", () => ({
  default: {
    react: vi.fn(),
    purge: vi.fn(),
  },
}));

function setPersistedState(value: unknown): void {
  window.localStorage.setItem(PERSISTED_WEB_STATE_STORAGE_KEY, JSON.stringify(value));
}

function persistedStateBase(): PersistedWebStateV1 {
  return {
    version: PERSISTED_WEB_STATE_VERSION,
    saved_at: "2026-01-01T00:00:00.000Z",
    strategy: {
      market_mode: "bear",
      price_segments: [{ price_low: 30000, price_high: 40000, weight: 100 }],
      time_segments: [],
    },
    use_draft: {
      now_price_input: 35500,
      custom_timestamp_input: "2026-01-10T10:00:00.000Z",
      custom_price_input: 35200,
      portfolio_timestamp_input: "2026-01-11T11:30:00.000Z",
      portfolio_price_input: 34900,
      portfolio_usd_input: 9999,
      portfolio_asset_input: 0.7,
      portfolio_avg_entry_price_input: "31000",
    },
    ui: {
      mode: "use",
      chart_timestamp: "2026-01-12T09:45:00.000Z",
    },
  };
}

describe("App", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
    window.localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const payload = init?.body ? JSON.parse(String(init.body)) : {};

        if (url.endsWith("/v1/evaluate/rows")) {
          const rows = Array.isArray(payload.rows) ? payload.rows : [];
          return {
            ok: true,
            status: 200,
            json: async () => ({
              rows: rows.map((row: { timestamp: string; price: number }) => ({
                timestamp: row.timestamp,
                price: row.price,
                time_k: 1,
                virtual_price: row.price,
                base_share: 0.25,
                target_share: 0.5,
              })),
            }),
          };
        }

        if (url.endsWith("/v1/evaluate/rows-from-ranges")) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              rows: [],
            }),
          };
        }

        if (url.endsWith("/v1/evaluate/point")) {
          const price = Number(payload.price ?? 50000);
          const timestamp = String(payload.timestamp ?? "2026-01-01T00:00:00Z");

          return {
            ok: true,
            status: 200,
            json: async () => ({
              row: {
                timestamp,
                price,
                time_k: 1,
                virtual_price: price,
                base_share: 0.33,
                target_share: 0.44,
              },
            }),
          };
        }

        if (url.endsWith("/v1/evaluate/portfolio")) {
          const price = Number(payload.price ?? 50000);
          const timestamp = String(payload.timestamp ?? "2026-01-01T00:00:00Z");

          return {
            ok: true,
            status: 200,
            json: async () => ({
              portfolio: {
                timestamp,
                price,
                time_k: 1,
                virtual_price: price,
                base_share: 0.35,
                target_share: 0.5,
                share_deviation: -0.15,
                portfolio_value_usd: 20000,
                asset_value_usd: 7000,
                usd_value_usd: 13000,
                target_asset_value_usd: 10000,
                target_asset_amount: 0.2,
                asset_amount_delta: -0.05,
                usd_delta: 2500,
                alignment_price: 48000,
                avg_entry_price: 42000,
                avg_entry_pnl_usd: 500,
                avg_entry_pnl_pct: 0.1,
              },
            }),
          };
        }

        return {
          ok: false,
          status: 404,
          json: async () => ({ error: { message: "Not found" } }),
        };
      }),
    );
  });

  afterEach(() => {
    window.history.replaceState({}, "", "/");
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("switches between Create and Use modes", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Create" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Use" }));
    expect(screen.getByRole("heading", { name: "Use" })).toBeInTheDocument();
  });

  it("applies JSON into form state", async () => {
    render(<App />);

    const textarea = screen.getByLabelText(/strategy json/i);
    fireEvent.change(textarea, {
      target: {
        value: JSON.stringify(
          {
            market_mode: "bull",
            price_segments: [{ price_low: 10000, price_high: 20000, weight: 1 }],
            time_segments: [],
          },
          null,
          2,
        ),
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Apply JSON" }));

    await waitFor(() => {
      expect(screen.getByText("JSON applied.")).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue("bull")).toBeInTheDocument();
  });

  it("shows JSON parse error without breaking form", () => {
    render(<App />);

    const textarea = screen.getByLabelText(/strategy json/i);
    fireEvent.change(textarea, { target: { value: "{" } });

    fireEvent.click(screen.getByRole("button", { name: "Apply JSON" }));

    expect(screen.getByText("Input is not valid JSON.")).toBeInTheDocument();
    expect(screen.getByDisplayValue("bear")).toBeInTheDocument();
  });

  it("evaluates now point in Use mode", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Use" }));
    fireEvent.click(screen.getByRole("button", { name: "Evaluate now" }));

    await waitFor(() => {
      expect(
        screen.getByText(/share with time modifier:\s*44\.00%/i),
      ).toBeInTheDocument();
    });
  });

  it("shows no time segments status", () => {
    render(<App />);

    expect(screen.getAllByText("No time segments").length).toBeGreaterThan(0);
  });

  it("keeps chart time input controlled in Use mode", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Use" }));

    const chartTimeInput = screen.getByLabelText("Chart time") as HTMLInputElement;
    expect(chartTimeInput.value).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);

    fireEvent.change(chartTimeInput, { target: { value: "2026-01-15T12:30" } });

    await waitFor(() => {
      expect(chartTimeInput.value).toBe("2026-01-15T12:30");
    });
  });

  it("adds a price segment with strictly positive lower bound", async () => {
    render(<App />);

    const textarea = screen.getByLabelText(/strategy json/i);
    fireEvent.change(textarea, {
      target: {
        value: JSON.stringify(
          {
            market_mode: "bear",
            price_segments: [{ price_low: 1, price_high: 2, weight: 100 }],
            time_segments: [],
          },
          null,
          2,
        ),
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Apply JSON" }));

    await waitFor(() => {
      expect(screen.getByText("JSON applied.")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "Add row" })[0]);

    const priceLowInputs = screen
      .getAllByLabelText(/^price_low$/i)
      .map((input) => Number((input as HTMLInputElement).value));

    expect(priceLowInputs.every((value) => value > 0)).toBe(true);
  });

  it("clamps now price to a positive value before evaluation", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Use" }));

    const nowPriceInput = screen.getAllByLabelText(/^price$/i)[0] as HTMLInputElement;
    expect(nowPriceInput).toHaveAttribute("min", "0.01");

    fireEvent.change(nowPriceInput, { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Evaluate now" }));

    await waitFor(() => {
      expect(screen.getByText(/price:\s*\$0\.01/i)).toBeInTheDocument();
    });
  });

  it("evaluates portfolio snapshot in Use mode", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Use" }));
    fireEvent.click(screen.getByRole("button", { name: "Evaluate portfolio" }));

    await waitFor(() => {
      expect(screen.getByText(/alignment price:\s*\$48,000\.00/i)).toBeInTheDocument();
    });
  });

  it("hydrates strategy and use draft from localStorage", () => {
    const state = persistedStateBase();
    state.strategy.market_mode = "bull";
    setPersistedState(state);

    render(<App />);

    expect(screen.getByRole("heading", { name: "Use" })).toBeInTheDocument();

    const nowPriceInput = screen.getAllByLabelText(/^price$/i)[0] as HTMLInputElement;
    const customTimestampInput = screen.getAllByLabelText(/^timestamp$/i)[0] as HTMLInputElement;
    const portfolioTimestampInput = screen.getAllByLabelText(/^timestamp$/i)[1] as HTMLInputElement;
    const chartTimeInput = screen.getByLabelText("Chart time") as HTMLInputElement;
    const usdInput = screen.getByLabelText("usd_amount") as HTMLInputElement;
    const avgEntryInput = screen.getByLabelText(
      "avg_entry_price (optional)",
    ) as HTMLInputElement;

    expect(nowPriceInput.value).toBe("35500");
    expect(customTimestampInput.value).toBe(
      toLocalDateTimeInput(state.use_draft!.custom_timestamp_input),
    );
    expect(portfolioTimestampInput.value).toBe(
      toLocalDateTimeInput(state.use_draft!.portfolio_timestamp_input),
    );
    expect(chartTimeInput.value).toBe(toLocalDateTimeInput(state.ui!.chart_timestamp));
    expect(usdInput.value).toBe("9999");
    expect(avgEntryInput.value).toBe("31000");
    expect(screen.queryByText(/share with time modifier:/i)).not.toBeInTheDocument();
  });

  it("falls back to defaults on corrupted persisted payload", () => {
    window.localStorage.setItem(PERSISTED_WEB_STATE_STORAGE_KEY, "{");

    render(<App />);

    expect(screen.getByRole("heading", { name: "Create" })).toBeInTheDocument();
    expect(screen.getByDisplayValue("bear")).toBeInTheDocument();
  });

  it("ignores persisted payload with invalid strategy", () => {
    const state = persistedStateBase();
    state.strategy = {
      market_mode: "bear",
      price_segments: [{ price_low: 10, price_high: 20, weight: 0 }],
      time_segments: [],
    };
    setPersistedState(state);

    render(<App />);

    expect(screen.getByRole("heading", { name: "Create" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Use" }));

    const nowPriceInput = screen.getAllByLabelText(/^price$/i)[0] as HTMLInputElement;
    expect(nowPriceInput.value).toBe("35000");
  });

  it("ignores persisted payload with unsupported version", () => {
    const state = persistedStateBase() as unknown as { version: number };
    state.version = 999;
    setPersistedState(state);

    render(<App />);

    expect(screen.getByRole("heading", { name: "Create" })).toBeInTheDocument();
  });

  it("uses weighted strategy default price when use draft is absent", () => {
    const state = persistedStateBase();
    state.strategy = {
      market_mode: "bear",
      price_segments: [
        { price_low: 100, price_high: 200, weight: 10 },
        { price_low: 400, price_high: 500, weight: 90 },
      ],
      time_segments: [],
    };
    delete state.use_draft;
    setPersistedState(state);

    render(<App />);

    const nowPriceInput = screen.getAllByLabelText(/^price$/i)[0] as HTMLInputElement;
    expect(nowPriceInput.value).toBe("420");
  });

  it("persists strategy, use draft and ui mode updates", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Use" }));

    const nowPriceInput = screen.getAllByLabelText(/^price$/i)[0] as HTMLInputElement;
    fireEvent.change(nowPriceInput, { target: { value: "36500" } });

    await waitFor(() => {
      const raw = window.localStorage.getItem(PERSISTED_WEB_STATE_STORAGE_KEY);
      expect(raw).not.toBeNull();

      const payload = JSON.parse(String(raw)) as PersistedWebStateV1;
      expect(payload.ui?.mode).toBe("use");
      expect(payload.use_draft?.now_price_input).toBe(36500);
    });

    fireEvent.click(screen.getByRole("tab", { name: "Create" }));
    fireEvent.change(screen.getByLabelText("market_mode"), { target: { value: "bull" } });

    await waitFor(() => {
      const raw = window.localStorage.getItem(PERSISTED_WEB_STATE_STORAGE_KEY);
      expect(raw).not.toBeNull();

      const payload = JSON.parse(String(raw)) as PersistedWebStateV1;
      expect(payload.ui?.mode).toBe("create");
      expect(payload.strategy.market_mode).toBe("bull");
    });
  });
});
