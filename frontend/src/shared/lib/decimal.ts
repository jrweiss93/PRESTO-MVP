/**
 * Aritmética decimal exacta sobre los importes que devuelve la API.
 *
 * Los montos llegan como texto decimal (`Decimal` de Django serializado por
 * DRF) y la regla del proyecto es no convertirlos nunca a `number`: se
 * comparan y se suman con enterosbigint, así el resultado es exactamente el
 * que devolvió el backend.
 */

const DECIMAL_PATTERN = /^[+-]?\d+(?:\.\d+)?$/;

type Scaled = {
  units: bigint;
  scale: number;
};

function parseDecimal(value: string): Scaled {
  const raw = (value ?? "").trim();
  if (!DECIMAL_PATTERN.test(raw)) {
    throw new Error(`Monto inválido: "${value}"`);
  }
  const negative = raw.startsWith("-");
  const unsigned = negative ? raw.slice(1) : raw;
  const [integerPart, fractionPart = ""] = unsigned.split(".");
  const units = BigInt(`${integerPart}${fractionPart}`) * (negative ? -1n : 1n);
  return { units, scale: fractionPart.length };
}

function rescale(units: bigint, from: number, to: number): bigint {
  if (from === to) return units;
  return from < to ? units * 10n ** BigInt(to - from) : units;
}

function formatScaled(units: bigint, scale: number): string {
  const negative = units < 0n;
  const absolute = negative ? -units : units;
  if (scale === 0) return `${negative ? "-" : ""}${absolute}`;
  const base = 10n ** BigInt(scale);
  const integer = absolute / base;
  const fraction = (absolute % base).toString().padStart(scale, "0");
  return `${negative ? "-" : ""}${integer}.${fraction}`;
}

/**
 * Compara dos importes decimales sin convertirlos a `number`.
 *
 * @returns `-1` si `a` es menor, `0` si son iguales y `1` si `a` es mayor.
 */
export function compareDecimals(a: string, b: string): number {
  const left = parseDecimal(a);
  const right = parseDecimal(b);
  const scale = Math.max(left.scale, right.scale);
  const leftUnits = rescale(left.units, left.scale, scale);
  const rightUnits = rescale(right.units, right.scale, scale);
  if (leftUnits === rightUnits) return 0;
  return leftUnits < rightUnits ? -1 : 1;
}

/** Suma importes decimales y devuelve el resultado como texto decimal. */
export function sumDecimals(values: readonly string[]): string {
  if (values.length === 0) return "0";
  const parsed = values.map(parseDecimal);
  const scale = Math.max(...parsed.map((item) => item.scale));
  const total = parsed.reduce(
    (acc, item) => acc + rescale(item.units, item.scale, scale),
    0n,
  );
  return formatScaled(total, scale);
}

/**
 * Porcentaje que representa `part` sobre `total`, con dos decimales.
 *
 * Se usa para las barras de progreso (un porcentaje no es un monto), pero se
 * calcula con enteros para no arrastrar errores de coma flotante.
 */
export function decimalPercent(part: string, total: string): number {
  const parsedPart = parseDecimal(part);
  const parsedTotal = parseDecimal(total);
  const scale = Math.max(parsedPart.scale, parsedTotal.scale);
  const partUnits = rescale(parsedPart.units, parsedPart.scale, scale);
  const totalUnits = rescale(parsedTotal.units, parsedTotal.scale, scale);
  if (totalUnits === 0n) return 0;
  const hundredths = (partUnits * 10000n) / totalUnits;
  return Number(hundredths) / 100;
}
