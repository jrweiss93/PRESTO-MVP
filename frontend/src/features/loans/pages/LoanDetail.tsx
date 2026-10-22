import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { Installment, LoanDetail } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import {
  INSTALLMENT_STATUS_LABELS,
  LOAN_STATUS_LABELS,
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
  const payables = loan.installments.filter(
    (i: Installment) => i.status === "pending" || i.status === "overdue",
  );

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
        <h2>Términos originales (snapshot inmutable)</h2>
        <pre className="mono" style={{ whiteSpace: "pre-wrap", margin: 0 }}>
          {JSON.stringify(loan.terms_snapshot.snapshot_data, null, 2)}
        </pre>
        <p className="small text-muted" style={{ marginBottom: 0 }}>
          Registrado {formatDateTime(loan.terms_snapshot.accepted_at)} ·{" "}
          {loan.terms_snapshot.is_immutable ? "Inmutable" : "Mutable"}
        </p>
      </div>
    </>
  );
}
