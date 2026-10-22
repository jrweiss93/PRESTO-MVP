// Cliente HTTP: una sola capa de acceso a la API (PROYECTO_FRONT.md §4.3).
//
// Reglas de sesión (PROYECTO_FRONT.md §6.2 y ADR 0014 del backend):
// - el **access token vive solo en memoria**: nunca en localStorage ni
//   sessionStorage;
// - el **refresh token no lo ve el front**: viaja en la cookie httpOnly
//   `presto_refresh` que deja el backend, así que el refresh se pide con
//   `credentials: "include"` y sin cuerpo.

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ErrorBody {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
  detail?: string;
}

/** Saca un mensaje legible del cuerpo de error del backend. */
export function extractErrorMessage(status: number, body: unknown): string {
  if (body && typeof body === "object") {
    const obj = body as ErrorBody;
    if (obj.error?.message) return obj.error.message;
    if (typeof obj.detail === "string") return obj.detail;
    const parts: string[] = [];
    for (const [key, value] of Object.entries(body)) {
      if (Array.isArray(value)) {
        parts.push(`${key}: ${value.join(", ")}`);
      } else if (typeof value === "string") {
        parts.push(`${key}: ${value}`);
      }
    }
    if (parts.length > 0) return parts.join(" · ");
  }
  return `Error ${status}`;
}

async function rawRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (res.status === 204) return undefined as T;

  let body: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, extractErrorMessage(res.status, body), body);
  }
  return body as T;
}

/**
 * Renueva el access token con el refresh que tiene el backend en la cookie
 * httpOnly. Si el backend todavía devuelve el refresh en el cuerpo, se acepta
 * por compatibilidad.
 */
async function tryRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (!res.ok) return false;
    const data = (await res.json()) as {
      access?: string;
      refresh?: string;
    };
    if (!data.access) return false;
    setAccessToken(data.access);
    return true;
  } catch {
    return false;
  }
}

/** Realiza una petición autenticada; renueva el token y reintenta ante un 401. */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  try {
    return await rawRequest<T>(path, options);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      const refreshed = await tryRefresh();
      if (refreshed) {
        return await rawRequest<T>(path, options);
      }
      setAccessToken(null);
    }
    throw err;
  }
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

/**
 * Toda operación que mueve dinero es idempotente: el backend exige el header
 * `Idempotency-Key` (PROYECTO_FRONT.md §6.1). La clave se genera una vez por
 * intento del usuario y se reutiliza en los reintentos.
 */
export function apiPostWithIdempotency<T>(
  path: string,
  body: unknown,
  idempotencyKey: string,
): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

/** Genera la clave de idempotencia de un intento del usuario. */
export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `key-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/**
 * Algunos endpoints de lista del schema devuelven una referencia simple
 * (drf-spectacular) aunque en realidad responden una página paginada.
 * Normalizamos las dos formas.
 */
export function asArray<T>(data: T | T[] | null | undefined): T[] {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  if (typeof data === "object" && "results" in (data as object)) {
    const results = (data as unknown as { results: T[] }).results;
    return Array.isArray(results) ? results : [];
  }
  return [data];
}

/** Igual que `asArray`, pero para las respuestas paginadas del backend. */
export function asPage<T>(
  data: T | T[] | { results?: T[] } | null | undefined,
): T[] {
  return asArray(data as T | T[] | null | undefined);
}
