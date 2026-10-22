import { expect, type Page, type TestInfo } from "@playwright/test";

/**
 * Datos de las cuentas de prueba de cada proyecto.
 *
 * - `mock`: las cuentas que trae el mock en memoria.
 * - `api`: las personas que siembra `manage.py seed_demo` en el backend.
 */
export const CREDENTIALS = {
  mock: { email: "demo@presto.com", password: "demo123456" },
  api: { email: "ana@presto.demo", password: "Presto123!" },
} as const;

export function credentialsFor(projectName: string) {
  return CREDENTIALS[projectName === "api" ? "api" : "mock"];
}

/** Se salta el test si la API real no está levantada. */
export async function skipIfApiUnavailable(testInfo: TestInfo) {
  if (testInfo.project.name !== "api") return;
  const response = await fetch("http://127.0.0.1:8000/api/v1/meta/").catch(
    () => null,
  );
  if (!response || !response.ok) {
    testInfo.annotations.push({
      type: "skip",
      description:
        "La API real no está disponible en http://127.0.0.1:8000 (levantá el backend con seed_demo para correr este proyecto)",
    });
    testInfo.skip(true, "API real no disponible");
  }
}

/** Inicia sesión en la app con las credenciales del proyecto. */
export async function login(page: Page, projectName: string) {
  const { email, password } = credentialsFor(projectName);
  await page.goto("/login");
  await page.getByLabel(/^Email/).fill(email);
  await page.getByLabel(/^Contraseña/).fill(password);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}
