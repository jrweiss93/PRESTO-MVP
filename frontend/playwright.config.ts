import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end de los flujos críticos (PROYECTO_FRONT.md §6.4): registro/login,
 * depósito y aceptación de una oferta.
 *
 * Hay dos proyectos:
 *
 * - `mock`: el front contra el mock en memoria (puerto 8001). No necesita el
 *   backend, así que corre en cualquier máquina.
 * - `api`: el front contra la API real de Django (puerto 8000). Necesita el
 *   backend con `manage.py seed_demo`; si no está, los tests se saltan.
 *
 * `webServer` es una opción global de Playwright: se levantan el mock y las
 * dos instancias de Vite (una apuntando al mock y otra a la API real).
 */
const MOCK_API = "http://127.0.0.1:8001";
const REAL_API = "http://127.0.0.1:8000";
const MOCK_WEB = "http://127.0.0.1:4181";
const API_WEB = "http://127.0.0.1:4182";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    locale: "es-AR",
  },
  webServer: [
    {
      command: "pnpm mock",
      url: `${MOCK_API}/api/v1/meta/`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "pnpm dev --port 4181 --strictPort --host 127.0.0.1",
      url: MOCK_WEB,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: { VITE_API_URL: `${MOCK_API}/api/v1` },
    },
    {
      command: "pnpm dev --port 4182 --strictPort --host 127.0.0.1",
      url: API_WEB,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: { VITE_API_URL: `${REAL_API}/api/v1` },
    },
  ],
  projects: [
    {
      name: "mock",
      use: { ...devices["Desktop Chrome"], baseURL: MOCK_WEB },
    },
    {
      name: "api",
      use: { ...devices["Desktop Chrome"], baseURL: API_WEB },
    },
  ],
});
