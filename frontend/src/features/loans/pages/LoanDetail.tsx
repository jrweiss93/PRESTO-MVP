import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { Installment, LoanDetail } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import {
  INSTALLMENT_STATUS_LABELS,
  LOAN_STATUS_LABELS,
  currencyLabel,
  formatDate,
  formatDateTime,
  formatMoney,
  formatRate,
} from "@/shared/lib/format";

const INSTALLMENT_BADGE: Record<string, string> = {
  pending: "warning",
  paid: "success",
  overdue: "danger",
};

type SnapshotTerms = {
  amount?: unknown;
  currency?: unknown;
  interest_rate?: unknown;
  term_months?: unknown;
  requirements?: unknown;
};

function readSnapshotTerms(value: unknown): SnapshotTerms {
  return value && typeof value === "object" ? (value as SnapshotTerms) : {};
}

export default function LoanDetailPage() {
  const { loanId } = useParams<{ loanId: string }>();
  const { user } = useAuth();
  const [loan, setLoan] = useState<LoanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [payingNumber, setPayingNumber] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!loanId) return;
    try {
      setLoan(await api.getLoan(loanId));
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo cargar el préstamo.",
      );
    } finally {
      setLoading(false);
    }
  }, [loanId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handlePay(number: number) {
    if (!loanId) return;
    setPayingNumber(number);
    setError(null);
    setNotice(null);
    try {
      await api.payInstallment(loanId, number);
      setNotice(`Cuota ${number} pagada.`);
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "No se pudo pagar la cuota.",
      );
    } finally {
      setPayingNumber(null);
    }
  }

  if (loading) return <div className="loading">Cargando préstamo…</div>;
  if (!loan) {
    return (
      <>
        <h1>Préstamo</h1>
        <div className="alert error">{error ?? "Préstamo no encontrado."}</div>
        <Link to="/prestamos">Volver a préstamos</Link>
      </>
    );
  }

  const isBorrower = loan.borrower_user_id === user?.id;
  const counterpartEmail = isBorrower ? loan.lender_email : loan.borrower_email;
  const payables = loan.installments.filter(
    (i: Installment) => i.status === "pending" || i.status === "overdue",
  );

  const snapshot = readSnapshotTerms(loan.terms_snapshot.snapshot_data);
  const snapshotCurrency =
    typeof snapshot.currency === "string" ? snapshot.currency : loan.currency;
  const snapshotAmount =
    typeof snapshot.amount === "string" ? snapshot.amount : loan.principal;
  const snapshotRate =
    typeof snapshot.interest_rate === "string"
      ? snapshot.interest_rate
      : loan.interest_rate;
  const snapshotTerm =
    typeof snapshot.term_months === "number"
      ? snapshot.term_months
      : loan.term_months;
  const snapshotRequirements =
    typeof snapshot.requirements === "string" &&
    snapshot.requirements.trim() !== ""
      ? snapshot.requirements
      : null;

  return (
    <>
      <p className="small">
        <Link to="/prestamos">← Préstamos</Link>
      </p>
      <h1>Detalle del préstamo</h1>
      <p className="page-subtitle">
        {isBorrower ? "Sos prestatario" : "Sos prestamista"} ·{" "}
        <span
          className={`badge ${loan.status === "active" ? "info" : loan.status === "paid" ? "success" : "danger"}`}
        >
          {LOAN_STATUS_LABELS[loan.status]}
        </span>
      </p>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <div className="card-grid">
        <div className="stat-card">
          <div className="label">Capital</div>
          <div className="value">
            {formatMoney(loan.principal, loan.currency)}
          </div>
        </div>
        <div className="stat-card">
          <div className="label">Tasa</div>
          <div className="value">{formatRate(loan.interest_rate)}</div>
        </div>
        <div className="stat-card">
          <div className="label">Plazo</div>
          <div className="value">{loan.term_months} meses</div>
        </div>
        <div className="stat-card">
          <div className="label">Aceptado</div>
          <div className="value" style={{ fontSize: "1rem" }}>
            {formatDateTime(loan.accepted_at)}
          </div>
        </div>
      </div>

      {counterpartEmail && (
        <div className="card">
          <h2>Contacto</h2>
          <p className="mb-0">
            {isBorrower ? "Prestamista" : "Prestatario"}:{" "}
            <a
              className="text-brand-500 hover:text-brand-600"
              href={`mailto:${counterpartEmail}`}
            >
              {counterpartEmail}
            </a>
          </p>
        </div>
      )}

      <div className="card">
        <h2>Cuotas</h2>
        {loan.installments.length === 0 ? (
          <div className="empty-state">
            Este préstamo no tiene cuotas registradas.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Vencimiento</th>
                  <th>Capital</th>
                  <th>Interés</th>
                  <th>Total</th>
                  <th>Estado</th>
                  <th>Pagada</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {loan.installments.map((inst) => (
                  <tr key={inst.id}>
                    <td>{inst.number}</td>
                    <td>{formatDate(inst.due_date)}</td>
                    <td>{formatMoney(inst.principal_amount, loan.currency)}</td>
                    <td>{formatMoney(inst.interest_amount, loan.currency)}</td>
                    <td>
                      <strong>{formatMoney(inst.amount, loan.currency)}</strong>
                    </td>
                    <td>
                      <span
                        className={`badge ${INSTALLMENT_BADGE[inst.status] ?? ""}`}
                      >
                        {INSTALLMENT_STATUS_LABELS[inst.status]}
                      </span>
                    </td>
                    <td>{formatDateTime(inst.paid_at)}</td>
                    <td>
                      {isBorrower &&
                        (inst.status === "pending" ||
                          inst.status === "overdue") && (
                          <button
                            className="btn small"
                            onClick={() => handlePay(inst.number)}
                            disabled={payingNumber === inst.number}
                          >
                            {payingNumber === inst.number
                              ? "Pagando…"
                              : `Pagar cuota ${inst.number}`}
                          </button>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {isBorrower && payables.length > 0 && (
          <p className="small text-muted" style={{ marginTop: "0.75rem" }}>
            Podés pagar{" "}
            {payables.length === 1
              ? "la cuota pendiente"
              : "las cuotas pendientes"}{" "}
            desde la tabla. Los fondos se debitán de tu billetera.
          </p>
        )}
      </div>

      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="mb-1">Condiciones aceptadas</h2>
            <p className="text-theme-sm text-gray-500">
              Copia exacta de la oferta al cerrar el préstamo. Aunque la oferta
              original cambie o se elimine, estas condiciones no se modifican.
            </p>
          </div>
          <span
            className={`badge ${loan.terms_snapshot.is_immutable ? "success" : "warning"}`}
          >
            {loan.terms_snapshot.is_immutable ? "Inmutable" : "Mutable"}
          </span>
        </div>

        <dl className="mt-5 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-3">
          <div>
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Monto
            </dt>
            <dd className="mt-1 text-theme-sm font-medium text-gray-800">
              {formatMoney(snapshotAmount, snapshotCurrency)}
            </dd>
          </div>
          <div>
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Tasa
            </dt>
            <dd className="mt-1 text-theme-sm font-medium text-gray-800">
              {formatRate(snapshotRate)}
            </dd>
          </div>
          <div>
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Plazo
            </dt>
            <dd className="mt-1 text-theme-sm font-medium text-gray-800">
              {snapshotTerm} meses
            </dd>
          </div>
          <div>
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Moneda
            </dt>
            <dd className="mt-1 text-theme-sm font-medium text-gray-800">
              {currencyLabel(snapshotCurrency)}
            </dd>
          </div>
          <div>
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Aceptado por
            </dt>
            <dd className="mt-1 text-theme-sm font-medium text-gray-800">
              {loan.borrower_email}
            </dd>
          </div>
          <div>
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Fecha de aceptación
            </dt>
            <dd className="mt-1 text-theme-sm font-medium text-gray-800">
              {formatDateTime(loan.terms_snapshot.accepted_at)}
            </dd>
          </div>
          <div className="sm:col-span-2 xl:col-span-3">
            <dt className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
              Requisitos de la oferta
            </dt>
            <dd className="mt-1 text-theme-sm text-gray-700">
              {snapshotRequirements ?? "Sin requisitos adicionales."}
            </dd>
          </div>
        </dl>

        <details className="mt-5">
          <summary className="cursor-pointer text-theme-sm font-medium text-brand-500 hover:text-brand-600">
            Ver datos técnicos
          </summary>
          <pre className="mono mt-3 overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-4 text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">
            {JSON.stringify(loan.terms_snapshot.snapshot_data, null, 2)}
          </pre>
        </details>
      </div>
    </>
  );
}
