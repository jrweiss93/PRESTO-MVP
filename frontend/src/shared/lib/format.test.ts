import { describe, expect, it } from "vitest";
import { formatMoney, formatPercent, formatRate } from "./format";

describe("formatMoney", () => {
  it("formatea el importe exacto que devuelve la API", () => {
    expect(formatMoney("1234.50", "ARS")).toBe("$ 1.234,50");
    expect(formatMoney("1000000.00", "ARS")).toBe("$ 1.000.000,00");
  });

  it("no arrastra errores de coma flotante", () => {
    // 0.1 + 0.2 en float da 0.30000000000000004
    expect(formatMoney("0.30", "USD")).toBe("US$ 0,30");
    expect(formatMoney("12345678901234.99", "ARS")).toBe(
      "$ 12.345.678.901.234,99",
    );
  });

  it("usa dos decimales por defecto", () => {
    expect(formatMoney("10", "ARS")).toBe("$ 10,00");
    expect(formatMoney("10.5", "ARS")).toBe("$ 10,50");
  });

  it("devuelve un guion cuando no hay importe", () => {
    expect(formatMoney(null)).toBe("—");
    expect(formatMoney(undefined, "ARS")).toBe("—");
    expect(formatMoney("", "ARS")).toBe("—");
  });
});

describe("formatRate", () => {
  it("agrega la TNA", () => {
    expect(formatRate("32.00")).toBe("32,00% TNA");
    expect(formatRate(18)).toBe("18,00% TNA");
  });
});

describe("formatPercent", () => {
  it("formatea porcentajes sin decimales de sobra", () => {
    expect(formatPercent(50)).toBe("50%");
    expect(formatPercent("12.50")).toBe("12,5%");
  });
});
