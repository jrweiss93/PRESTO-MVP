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
  const { user } = useAuth();
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

  return (
    <>
      <h1>Préstamos</h1>
      <p className="page-subtitle">
        Los préstamos en los que participás como prestatario o prestamista.
      </p>

      {error && <div className="alert error">{error}</div>}

      <div className="card">
        {loading ? (
          <div className="loading">Cargando…</div>
        ) : loans.length === 0 ? (
          <div className="empty-state">
            No tenés préstamos todavía. Buscá ofertas en el{" "}
            <Link to="/marketplace">marketplace</Link> para solicitar uno.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Rol</th>
                  <th>Capital</th>
                  <th>Tasa</th>
                  <th>Plazo</th>
                  <th>Estado</th>
                  <th>Aceptado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {loans.map((loan) => {
                  const isBorrower = loan.borrower_user_id === user?.id;
                  return (
                    <tr key={loan.id}>
                      <td>
                        <span
                          className={`badge ${isBorrower ? "warning" : "success"}`}
                        >
                          {isBorrower ? "Prestatario" : "Prestamista"}
                        </span>
                      </td>
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
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
