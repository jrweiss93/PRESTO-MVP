import { expect, test } from "@playwright/test";
import { login, skipIfApiUnavailable } from "./helpers";

test.describe("billetera", () => {
  test("registra un depósito y lo muestra en los movimientos", async ({
    page,
  }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await login(page, testInfo.project.name);

    await page.getByRole("link", { name: "Billetera" }).first().click();
    await expect(
      page.getByRole("heading", { level: 1, name: "Billetera" }),
    ).toBeVisible();

    const form = page.locator("form", {
      has: page.getByRole("button", { name: "Registrar movimiento" }),
    });
    await form.getByLabel("Importe").fill("1000");
    await page.getByRole("button", { name: "Registrar movimiento" }).click();

    await expect(page.locator(".alert.success")).toHaveText(
      "Movimiento registrado.",
    );
    await expect(page.locator("table.data tbody tr").first()).toBeVisible();
  });

  test("el botón se bloquea mientras se registra el movimiento", async ({
    page,
  }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await login(page, testInfo.project.name);
    await page.getByRole("link", { name: "Billetera" }).first().click();

    // Se retrasa la respuesta para poder observar el estado "Enviando…".
    await page.route(/\/ledger\/transactions\/$/, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.continue();
    });

    const form = page.locator("form", {
      has: page.getByRole("button", { name: "Registrar movimiento" }),
    });
    await form.getByLabel("Importe").fill("10");
    await page.getByRole("button", { name: "Registrar movimiento" }).click();

    // Mientras la petición está en curso el botón queda deshabilitado.
    await expect(
      page.getByRole("button", { name: "Enviando…" }),
    ).toBeDisabled();
    await expect(page.locator(".alert.success")).toBeVisible();
  });
});
