import type {
  InstallmentStatus,
  KYCStatus,
  LoanStatus,
  OfferStatus,
  PositionStatus,
} from "@/shared/api/types";

const SYMBOL_BY_CODE: Record<string, string> = {
  ARS: "$",
  USD: "US$",
};

/**
 * El backend manda los importes como texto decimal (`Decimal` de Django
 * serializado por DRF). Nunca se convierten con `parseFloat`: se separa la
 * parte entera de la decimal y se formatea el entero por grupos de miles,
 * así el valor mostrado es exactamente el que devolvió la API.
 */
function splitDecimal(value: string): {
  sign: string;
  integer: string;
  fraction: string;
} {
  const raw = value.trim();
  const match = /^([+-]?)(\d*)(?:\.(\d+))?$/.exec(raw);
  if (!match) return { sign: "", integer: "0", fraction: "" };
  const sign = match[1] === "-" ? "-" : "";
  const integer = match[2] || "0";
  const fraction = match[3] ?? "";
  return { sign, integer, fraction };
}

function groupThousands(digits: string): string {
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function formatDecimalString(value: string, minDecimals = 2): string {
  const { sign, integer, fraction } = splitDecimal(value);
  let frac = fraction.replace(/0+$/, "");
  if (frac.length < minDecimals) frac = frac.padEnd(minDecimals, "0");
  return `${sign}${groupThousands(integer)},${frac}`;
}

export function formatMoney(
  amount: string | number | null | undefined,
  currency?: string | null,
): string {
  if (amount === null || amount === undefined || amount === "") return "—";
  const symbol =
    currency && SYMBOL_BY_CODE[currency] !== undefined
      ? SYMBOL_BY_CODE[currency]
      : (currency ?? "");
  const text =
    typeof amount === "number"
      ? amount.toLocaleString("es-AR", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : formatDecimalString(amount);
  return `${symbol} ${text}`.trim();
}

export function formatRate(rate: string | number | null | undefined): string {
  if (rate === null || rate === undefined || rate === "") return "—";
  const text =
    typeof rate === "number"
      ? rate.toLocaleString("es-AR", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : formatDecimalString(rate);
  return `${text}% TNA`;
}

export function formatPercent(
  value: string | number | null | undefined,
): string {
  if (value === null || value === undefined || value === "") return "—";
  const text =
    typeof value === "number"
      ? value.toLocaleString("es-AR", { maximumFractionDigits: 2 })
      : formatDecimalString(value, 0);
  return `${text}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function currencyLabel(currency: string): string {
  return currency === "USD"
    ? "Dólar"
    : currency === "ARS"
      ? "Peso argentino"
      : currency;
}

export const OFFER_STATUS_LABELS: Record<OfferStatus, string> = {
  active: "Activa",
  expired: "Expirada",
  accepted: "Aceptada",
};

export const LOAN_STATUS_LABELS: Record<LoanStatus, string> = {
  active: "Activo",
  paid: "Pagado",
  defaulted: "En mora",
};

export const INSTALLMENT_STATUS_LABELS: Record<InstallmentStatus, string> = {
  pending: "Pendiente",
  paid: "Pagada",
  overdue: "Vencida",
};

export const POSITION_STATUS_LABELS: Record<PositionStatus, string> = {
  active: "Activa",
  matured: "Vencida",
};

export const KYC_STATUS_LABELS: Record<KYCStatus, string> = {
  pending: "Pendiente",
  approved: "Aprobada",
  rejected: "Rechazada",
};

export const TX_TYPE_LABELS: Record<string, string> = {
  deposit: "Depósito",
  withdrawal: "Retiro",
  transfer: "Transferencia",
  interest: "Interés",
  fee: "Comisión",
  reversal: "Reverso",
};
