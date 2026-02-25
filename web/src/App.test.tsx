import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

const VALID_STRATEGY_JSON = JSON.stringify(
  {
    market_mode: "bear",
    price_segments: [
      { price_low: 30000, price_high: 40000, weight: 40 },
      { price_low: 40000, price_high: 50000, weight: 60 },
    ],
    time_segments: [],
  },
  null,
  2,
);

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          row: {
            timestamp: "2026-01-01T00:00:00Z",
            price: 40000,
            time_k: 1,
            virtual_price: 40000,
            base_share: 0.333333,
            target_share: 0.444444,
          },
        }),
      }),
    );

    const clipboard = {
      writeText: vi.fn().mockResolvedValue(undefined),
    };
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: clipboard,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("parses valid strategy payload", async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText(/strategy json/i), {
      target: { value: VALID_STRATEGY_JSON },
    });
    fireEvent.click(screen.getByRole("button", { name: "Parse" }));

    expect(screen.getByText("Parsed successfully.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/target_share/i)).toBeInTheDocument();
    });
  });

  it("shows error for invalid JSON", () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText(/strategy json/i), {
      target: { value: "{" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Parse" }));

    expect(screen.getByText("Input is not valid JSON.")).toBeInTheDocument();
  });

  it("uploads file content into textarea exactly", async () => {
    render(<App />);

    const input = screen.getByLabelText(/upload \.json/i) as HTMLInputElement;
    const file = new File([VALID_STRATEGY_JSON], "strategy.json", { type: "application/json" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByLabelText(/strategy json/i)).toHaveValue(VALID_STRATEGY_JSON);
    });
  });

  it("maps API response and shows target_share", async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText(/strategy json/i), {
      target: { value: VALID_STRATEGY_JSON },
    });
    fireEvent.click(screen.getByRole("button", { name: "Parse" }));

    await waitFor(() => {
      expect(screen.getByText(/0\.444444/)).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalled();
  });
});
