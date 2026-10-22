import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "./endpoints";

const originalFetch = globalThis.fetch;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function lastCall(spy: ReturnType<typeof vi.fn>): [string, RequestInit] {
  const call = spy.mock.calls[spy.mock.calls.length - 1] as [
    string,
    RequestInit,
  ];
  return call;
}

describe("operaciones que mueven dinero", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("createTransaction manda el header Idempotency-Key", async () => {
    const spy = vi.fn(async () => jsonResponse({ id: "tx-1" }));
    globalThis.fetch = spy as unknown as typeof fetch;

    await api.createTransaction(
      { type: "deposit", currency: "ARS", amount: "1000.00" },
      "key-1",
    );

    const [, init] = lastCall(spy);
    expect((init.headers as Record<string, string>)["Idempotency-Key"]).toBe(
      "key-1",
    );
    expect(init.method).toBe("POST");
  });

  it("acceptOffer manda el header Idempotency-Key", async () => {
    const spy = vi.fn(async () => jsonResponse({ id: "loan-1" }));
    globalThis.fetch = spy as unknown as typeof fetch;

    await api.acceptOffer({ offer_id: "offer-1" }, "key-2");

    const [, init] = lastCall(spy);
    expect((init.headers as Record<string, string>)["Idempotency-Key"]).toBe(
      "key-2",
    );
  });

  it("openPosition manda el header Idempotency-Key", async () => {
    const spy = vi.fn(async () => jsonResponse({ id: "pos-1" }));
    globalThis.fetch = spy as unknown as typeof fetch;

    await api.openPosition(
      { product_id: "prod-1", amount: "500.00", currency: "ARS" },
      "key-3",
    );

    const [, init] = lastCall(spy);
    expect((init.headers as Record<string, string>)["Idempotency-Key"]).toBe(
      "key-3",
    );
  });

  it("createPayment manda el header Idempotency-Key", async () => {
    const spy = vi.fn(async () => jsonResponse({ id: "pay-1" }));
    globalThis.fetch = spy as unknown as typeof fetch;

    await api.createPayment(
      { direction: "transfer", amount: "100.00", currency: "ARS" },
      "key-4",
    );

    const [, init] = lastCall(spy);
    expect((init.headers as Record<string, string>)["Idempotency-Key"]).toBe(
      "key-4",
    );
  });

  it("las lecturas no mandan Idempotency-Key", async () => {
    const spy = vi.fn(async () => jsonResponse({ count: 0, results: [] }));
    globalThis.fetch = spy as unknown as typeof fetch;

    await api.listLoans();

    const [, init] = lastCall(spy);
    expect(init.method).toBeUndefined();
    expect(
      (init.headers as Record<string, string>)["Idempotency-Key"],
    ).toBeUndefined();
  });
});

describe("consultas de la API", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("getMeta devuelve el bloque de compliance", async () => {
    globalThis.fetch = vi.fn(async () =>
      jsonResponse({
        mode: "demo",
        simulated_money: true,
        compliance: {
          legal_review_pending: true,
          acknowledged: false,
          items: [{ id: "pla-ft", label: "PLA/FT", doc: "docs/x.md" }],
        },
      }),
    ) as unknown as typeof fetch;

    const meta = await api.getMeta();
    expect(meta.compliance.legal_review_pending).toBe(true);
    expect(meta.compliance.items).toHaveLength(1);
  });

  it("los reportes mandan la moneda y el rango", async () => {
    const spy = vi.fn(async () => jsonResponse({}));
    globalThis.fetch = spy as unknown as typeof fetch;

    await api.getSpendingReport({ currency: "ARS", from: "2026-10-01" });

    const [url] = lastCall(spy);
    expect(url).toContain("currency=ARS");
    expect(url).toContain("from=2026-10-01");
  });
});
