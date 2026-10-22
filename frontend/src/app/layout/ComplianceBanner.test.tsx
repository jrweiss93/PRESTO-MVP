import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ComplianceBanner from "./ComplianceBanner";

const originalFetch = globalThis.fetch;

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function mockMeta(meta: unknown) {
  globalThis.fetch = vi.fn(async () =>
    jsonResponse(meta),
  ) as unknown as typeof fetch;
}

const pending = {
  mode: "production",
  simulated_money: false,
  compliance: {
    legal_review_pending: true,
    acknowledged: false,
    items: [{ id: "pla-ft", label: "PLA/FT mínimo", doc: "docs/legal.md" }],
  },
};

describe("ComplianceBanner", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  it("muestra el recordatorio cuando la revisión legal está pendiente", async () => {
    mockMeta(pending);
    render(<ComplianceBanner />);

    await waitFor(() => {
      expect(screen.getByText(/revisión legal pendiente/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/PLA\/FT mínimo/)).toBeInTheDocument();
  });

  it("no muestra nada en modo demo (material de pitch)", async () => {
    mockMeta({ ...pending, mode: "demo" });
    const { container } = render(<ComplianceBanner />);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });

  it("no muestra nada si la revisión ya está reconocida", async () => {
    mockMeta({
      ...pending,
      compliance: { ...pending.compliance, acknowledged: true },
    });
    const { container } = render(<ComplianceBanner />);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });
});
