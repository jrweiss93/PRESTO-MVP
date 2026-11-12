import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { Loan } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import {
  LOAN_STATUS_LABELS,
  formatDateTime,
  formatMoney,
  formatRate,
} from "@/shared/lib/format";

const STATUS_BADGE: Record<string, string> = {
  active: "info",
  paid: "success",
  defaulted: "danger",
};

export default function Loans() {
  const { user, activeProfile } = useAuth();
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoans(await api.listLoans());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "No se pudieron cargar los préstamos.",
        );
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const isBorrower = activeProfile === "borrower";
  const roleLoans = loans.filter((loan) =>
    isBorrower
      ? loan.borrower_user_id === user?.id
      : loan.lender_user_id === user?.id,
  );

  function counterpartEmail(loan: Loan) {
    return isBorrower ? loan.lender_email : loan.borrower_email;
  }

  return (
    <>
      <h1>{isBorrower ? "Préstamos como prestatario" : "Préstamos como prestamista"}</h1>
      <p className="page-subtitle">
        {isBorrower
          ? "Los préstamos que pediste y las cuotas que tenés que pagar."
          : "Los préstamos que financiaste y las cuotas que vas a cobrar."}
      </p>

      {error && <div className="alert error">{error}</div>}

      <div className="card">
        {loading ? (
          <div className="loading">Cargando.</div>
        ) : roleLoans.length === 0 ? (
          <div className="empty-state">
            {isBorrower ? (
              <>
                Todavía no pediste ningún préstamo. Buscá ofertas en el{" "}
                <Link to="/marketplace">marketplace</Link> para solicitar uno.
              </>
            ) : (
              <>
                Todavía no financiaste ningún préstamo.{" "}
                <Link to="/ofertas">Publicá tu primera oferta</Link> para que un
                prestatario pueda encontrarte.
              </>
            )}
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>{isBorrower ? "Prestamista" : "Prestatario"}</th>
                  <th>Capital</th>
                  <th>Tasa</th>
                  <th>Plazo</th>
                  <th>Estado</th>
                  <th>Aceptado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {roleLoans.map((loan) => (
                  <tr key={loan.id}>
                    <td>{counterpartEmail(loan) ?? "—"}</td>
                    <td>{formatMoney(loan.principal, loan.currency)}</td>
                    <td>{formatRate(loan.interest_rate)}</td>
                    <td>{loan.term_months} meses</td>
                    <td>
                      <span
                        className={`badge ${STATUS_BADGE[loan.status] ?? ""}`}
                      >
                        {LOAN_STATUS_LABELS[loan.status]}
                      </span>
                    </td>
                    <td>{formatDateTime(loan.accepted_at)}</td>
                    <td>
                      <Link to={`/prestamos/${loan.id}`}>Ver detalle</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
