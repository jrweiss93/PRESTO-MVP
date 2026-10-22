import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  asArray,
  extractErrorMessage,
  getAccessToken,
  setAccessToken,
} from "./client";

const originalFetch = globalThis.fetch;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("extractErrorMessage", () => {
  it("usa el mensaje del formato de error del backend", () => {
    expect(
      extractErrorMessage(400, {
        error: { code: "validation_error", message: "Datos inválidos" },
      }),
    ).toBe("Datos inválidos");
  });

  it("cae en el `detail` de DRF", () => {
    expect(extractErrorMessage(404, { detail: "No encontrado" })).toBe(
      "No encontrado",
    );
  });

  it("arma un mensaje con los errores por campo", () => {
    const message = extractErrorMessage(400, {
      idempotency_key: ["El header `Idempotency-Key` es obligatorio."],
    });
    expect(message).toContain("Idempotency-Key");
  });
});

describe("asArray", () => {
  it("normaliza la página paginada del backend", () => {
    expect(asArray({ count: 1, results: [{ id: "a" }] })).toEqual([
      { id: "a" },
    ]);
  });

  it("devuelve una lista vacía cuando no hay datos", () => {
    expect(asArray(null)).toEqual([]);
    expect(asArray(undefined)).toEqual([]);
  });
});

describe("token en memoria", () => {
  afterEach(() => {
    setAccessToken(null);
  });

  it("guarda y devuelve el access token solo en memoria", () => {
    expect(getAccessToken()).toBeNull();
    setAccessToken("abc");
    expect(getAccessToken()).toBe("abc");
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
    expect(globalThis.localStorage.getItem("access")).toBeNull();
  });
});

describe("apiRequest", () => {
  beforeEach(() => {
    setAccessToken(null);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("envía el access token en el header Authorization", async () => {
    const spy = vi.fn(async () => jsonResponse({ ok: true }));
    globalThis.fetch = spy as unknown as typeof fetch;
    setAccessToken("token-1");

    const { apiGet } = await import("./client");
    await apiGet("/meta/");

    const [, init] = spy.mock.calls[0] as unknown as [string, RequestInit];
    expect((init.headers as Record<string, string>).Authorization).toBe(
      "Bearer token-1",
    );
    expect(init.credentials).toBe("include");
  });

  it("renueva el token ante un 401 y reintenta la petición", async () => {
    const responses = [
      jsonResponse({ detail: "no autorizado" }, 401),
      jsonResponse({ access: "token-2" }),
      jsonResponse({ ok: true }),
    ];
    let call = 0;
    const spy = vi.fn(async () => {
      const response = responses[call];
      call += 1;
      return response;
    });
    globalThis.fetch = spy as unknown as typeof fetch;

    const { apiGet } = await import("./client");
    const data = await apiGet("/auth/me/");

    expect(data).toEqual({ ok: true });
    expect(spy).toHaveBeenCalledTimes(3);
    expect(getAccessToken()).toBe("token-2");
  });

  it("expone el error del backend como ApiError", async () => {
    globalThis.fetch = vi.fn(async () =>
      jsonResponse({ error: { message: "Sin permisos" } }, 403),
    ) as unknown as typeof fetch;

    const { apiGet } = await import("./client");
    await expect(apiGet("/loans/")).rejects.toBeInstanceOf(ApiError);
  });
});
