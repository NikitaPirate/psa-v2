import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

vi.mock("plotly.js-dist-min", () => ({
  default: {
    react: vi.fn(),
    purge: vi.fn(),
  },
}));

describe("App", () => {
  beforeEach(() => {
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

        return {
          ok: false,
          status: 404,
          json: async () => ({ error: { message: "Not found" } }),
        };
      }),
    );
  });

  afterEach(() => {
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
});
