import { describe, expect, it } from "vitest";
import {
  compareDecimals,
  decimalPercent,
  sumDecimals,
} from "@/shared/lib/decimal";

describe("compareDecimals", () => {
  it("compara dos importes iguales", () => {
    expect(compareDecimals("1250.50", "1250.50")).toBe(0);
  });

  it("compara importes con distinta cantidad de decimales", () => {
    expect(compareDecimals("1250.5", "1250.50")).toBe(0);
    expect(compareDecimals("1250.50", "1250.51")).toBe(-1);
    expect(compareDecimals("1250.51", "1250.50")).toBe(1);
  });

  it("compara importes grandes sin perder precisión", () => {
    expect(compareDecimals("9007199254740993.01", "9007199254740993.02")).toBe(
      -1,
    );
  });

  it("ordena importes negativos", () => {
    expect(compareDecimals("-10.00", "-5.00")).toBe(-1);
    expect(compareDecimals("-5.00", "-10.00")).toBe(1);
  });

  it("falla con un importe que no es un decimal", () => {
    expect(() => compareDecimals("mil", "1.00")).toThrow(/Monto inválido/);
  });
});

describe("sumDecimals", () => {
  it("suma importes decimales exactos", () => {
    expect(sumDecimals(["1000.10", "2000.20", "0.05"])).toBe("3000.35");
  });

  it("suma importes con distinta escala", () => {
    expect(sumDecimals(["10.5", "0.50"])).toBe("11.00");
  });

  it("devuelve cero para una lista vacía", () => {
    expect(sumDecimals([])).toBe("0");
  });

  it("no pierde precisión con importes grandes", () => {
    expect(sumDecimals(["9007199254740993.01", "0.01"])).toBe(
      "9007199254740993.02",
    );
  });
});

describe("decimalPercent", () => {
  it("calcula el porcentaje de un importe sobre un total", () => {
    expect(decimalPercent("25.00", "100.00")).toBe(25);
    expect(decimalPercent("33.33", "100.00")).toBeCloseTo(33.33, 2);
  });

  it("devuelve 0 cuando el total es 0", () => {
    expect(decimalPercent("10.00", "0.00")).toBe(0);
  });

  it("puede pasar del 100%", () => {
    expect(decimalPercent("150.00", "100.00")).toBe(150);
  });
});
