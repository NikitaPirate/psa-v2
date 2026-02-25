import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RootApp } from "./RootApp";
import { docsPromptByLocale } from "./docs/prompt";

vi.mock("plotly.js-dist-min", () => ({
  default: {
    react: vi.fn(),
    purge: vi.fn(),
  },
}));

describe("RootApp docs routing", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({ rows: [] }),
      })),
    );
  });

  afterEach(() => {
    window.history.replaceState({}, "", "/");
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders main app on root path", () => {
    window.history.replaceState({}, "", "/");
    render(<RootApp />);

    expect(screen.getByRole("heading", { name: "PSA Web" })).toBeInTheDocument();
  });

  it("renders docs on /docs/en", () => {
    window.history.replaceState({}, "", "/docs/en");
    render(<RootApp />);

    expect(screen.getByRole("heading", { name: "PSA v2 Documentation" })).toBeInTheDocument();
  });

  it("renders docs on /docs/ru", () => {
    window.history.replaceState({}, "", "/docs/ru");
    render(<RootApp />);

    expect(screen.getByRole("heading", { name: "Документация PSA v2" })).toBeInTheDocument();
  });

  it("redirects /docs to /docs/en", async () => {
    window.history.replaceState({}, "", "/docs");
    render(<RootApp />);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/docs/en");
    });
  });

  it("falls back unsupported docs locale to /docs/en", async () => {
    window.history.replaceState({}, "", "/docs/de");
    render(<RootApp />);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/docs/en");
    });
  });

  it("switches docs locale using docs-local toggle", async () => {
    window.history.replaceState({}, "", "/docs/en");
    render(<RootApp />);

    fireEvent.click(screen.getByRole("button", { name: "RU" }));

    await waitFor(() => {
      expect(window.location.pathname).toBe("/docs/ru");
      expect(screen.getByRole("heading", { name: "Документация PSA v2" })).toBeInTheDocument();
    });
  });

  it("copies prompt with navigator.clipboard", async () => {
    window.history.replaceState({}, "", "/docs/en");
    const writeText = vi.fn(async () => undefined);

    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    render(<RootApp />);

    fireEvent.click(screen.getByRole("button", { name: "Copy prompt" }));

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(docsPromptByLocale("en"));
      expect(screen.getByText("Prompt copied.")).toBeInTheDocument();
    });
  });

  it("falls back to document.execCommand when clipboard API is unavailable", async () => {
    window.history.replaceState({}, "", "/docs/en");

    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: undefined,
    });

    const execCommand = vi.fn(() => true);
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<RootApp />);

    fireEvent.click(screen.getByRole("button", { name: "Copy prompt" }));

    await waitFor(() => {
      expect(execCommand).toHaveBeenCalledWith("copy");
      expect(screen.getByText("Prompt copied.")).toBeInTheDocument();
    });
  });

  it("includes Docs entry link in topbar", () => {
    window.history.replaceState({}, "", "/");
    render(<RootApp />);

    const link = screen.getByRole("link", { name: "Docs" });
    expect(link).toHaveAttribute("href", "/docs/en");
  });
});
