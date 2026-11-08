import type { ProfileKind } from "@/shared/api/types";

/** Nombre visible de cada perfil de Presto. */
export const PROFILE_LABELS: Record<ProfileKind, string> = {
  borrower: "Prestatario",
  lender: "Prestamista",
  investor: "Inversor",
};

/** Estrecha un string al tipo `ProfileKind`, o devuelve false. */
export function isProfileKind(value: string | null | undefined): value is ProfileKind {
  return value === "borrower" || value === "lender" || value === "investor";
}
