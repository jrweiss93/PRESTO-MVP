import { expect, test } from "@playwright/test";
import { login, skipIfApiUnavailable } from "./helpers";

test.describe("marketplace", () => {
  test("busca ofertas y acepta una", async ({ page }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await login(page, testInfo.project.name);

    await page.getByRole("link", { name: "Marketplace" }).first().click();
    await expect(
      page.getByRole("heading", { name: "Marketplace de préstamos" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Buscar ofertas" }).click();

    await expect(page.locator("table.data tbody tr").first()).toBeVisible();

    await page.getByRole("button", { name: "Aceptar" }).first().click();

    await expect(page).toHaveURL(/\/prestamos\/[0-9a-f-]{36}/);
    await expect(
      page.getByRole("heading", { name: /Préstamo/i }).first(),
    ).toBeVisible();
  });

  test("compara dos ofertas y marca la más barata", async ({
    page,
  }, testInfo) => {
    await skipIfApiUnavailable(testInfo);
    await login(page, testInfo.project.name);

    await page.getByRole("link", { name: "Marketplace" }).first().click();
    await page.getByRole("button", { name: "Buscar ofertas" }).click();
    await expect(page.locator("table.data tbody tr").first()).toBeVisible();

    const checkboxes = page.getByRole("checkbox", {
      name: "Seleccionar oferta para comparar",
    });
    await checkboxes.nth(0).check();
    await checkboxes.nth(1).check();

    await page.getByRole("button", { name: /Comparar seleccionadas/ }).click();

    await expect(
      page.getByRole("heading", { name: "Comparación de ofertas" }),
    ).toBeVisible();
    await expect(page.getByText("Más barata").first()).toBeVisible();
  });
});
