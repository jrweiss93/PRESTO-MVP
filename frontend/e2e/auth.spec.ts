import { expect, test } from "@playwright/test";
import { login, skipIfApiUnavailable } from "./helpers";

test.describe("sesión", () => {
  test("inicia sesión y entra al dashboard", async ({ page }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await login(page, testInfo.project.name);

    await expect(page.getByRole("heading", { level: 1 })).toContainText("Hola");
    await expect(page.locator(".stat-card").first()).toBeVisible();
  });

  test("muestra un error con credenciales inválidas", async ({
    page,
  }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await page.goto("/login");
    await page.getByLabel(/^Email/).fill("nadie@presto.demo");
    await page.getByLabel(/^Contraseña/).fill("claveIncorrecta123");
    await page.getByRole("button", { name: "Ingresar" }).click();

    await expect(page.locator(".alert.error")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("la sesión sobrevive a una recarga (refresh por cookie)", async ({
    page,
  }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await login(page, testInfo.project.name);

    await page.reload();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(
      page.getByRole("heading", { level: 1, name: /Hola/ }),
    ).toBeVisible();
  });

  test("registra una cuenta nueva y deja la sesión iniciada", async ({
    page,
  }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    const email = `e2e-${Date.now()}@presto.demo`;

    await page.goto("/registro");
    await page.getByLabel(/^Email/).fill(email);
    await page.getByLabel(/^Contraseña/).fill("ClaveSegura123");
    await page.getByLabel(/^Repetir contraseña/).fill("ClaveSegura123");
    await page.getByRole("button", { name: "Registrarme" }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Hola");
  });
});
