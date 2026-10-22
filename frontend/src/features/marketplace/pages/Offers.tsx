import { useCallback, useEffect, useState, type FormEvent } from "react";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { Currency, Offer } from "@/shared/api/types";
import {
  OFFER_STATUS_LABELS,
  formatDateTime,
  formatMoney,
  formatRate,
} from "@/shared/lib/format";

const STATUS_BADGE: Record<string, string> = {
  active: "success",
  expired: "warning",
  accepted: "info",
};

export default function Offers() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [form, setForm] = useState({
    amount: "",
    currency: "ARS" as Currency,
    interest_rate: "",
    term_months: "",
    requirements: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [expiringId, setExpiringId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setOffers(await api.listMyOffers());
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron cargar las ofertas.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      await api.createOffer({
        amount: form.amount,
        currency: form.currency,
        interest_rate: form.interest_rate,
        term_months: Number(form.term_months),
        requirements: form.requirements || undefined,
      });
      setNotice("Oferta publicada.");
      setForm({
        amount: "",
        currency: "ARS",
        interest_rate: "",
        term_months: "",
        requirements: "",
      });
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo publicar la oferta.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleExpire(offerId: string) {
    setExpiringId(offerId);
    setError(null);
    setNotice(null);
    try {
      await api.updateOffer(offerId, { status: "expired" });
      setNotice("Oferta expirada.");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "No se pudo expirar la oferta.",
      );
    } finally {
      setExpiringId(null);
    }
  }

  return (
    <>
      <h1>Mis ofertas</h1>
      <p className="page-subtitle">
        Publicá ofertas de préstamo como prestamista y gestioná su estado.
      </p>

      <div className="card">
        <h2>Publicar nueva oferta</h2>
        <form onSubmit={handleCreate}>
          <div className="form-grid">
            <label className="field">
              Monto a prestar
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required
              />
            </label>
            <label className="field">
              Moneda
              <select
                value={form.currency}
                onChange={(e) =>
                  setForm({ ...form, currency: e.target.value as Currency })
                }
              >
                <option value="ARS">Peso argentino (ARS)</option>
                <option value="USD">Dólar (USD)</option>
              </select>
            </label>
            <label className="field">
              Tasa anual TNA (%)
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.interest_rate}
                onChange={(e) =>
                  setForm({ ...form, interest_rate: e.target.value })
                }
                required
              />
            </label>
            <label className="field">
              Plazo (meses)
              <input
                type="number"
                min="1"
                value={form.term_months}
                onChange={(e) =>
                  setForm({ ...form, term_months: e.target.value })
                }
                required
              />
            </label>
            <label className="field full">
              Requisitos
              <textarea
                maxLength={2000}
                value={form.requirements}
                onChange={(e) =>
                  setForm({ ...form, requirements: e.target.value })
                }
                placeholder="Condiciones que deben cumplir los tomadores (opcional)"
              />
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button className="btn" type="submit" disabled={submitting}>
              {submitting ? "Publicando…" : "Publicar oferta"}
            </button>
          </div>
        </form>
      </div>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <div className="card">
        <h2>Ofertas publicadas</h2>
        {loading ? (
          <div className="loading">Cargando…</div>
        ) : offers.length === 0 ? (
          <div className="empty-state">Todavía no publicaste ofertas.</div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Monto</th>
                  <th>Tasa</th>
                  <th>Plazo</th>
                  <th>Estado</th>
                  <th>Creada</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {offers.map((o) => (
                  <tr key={o.id}>
                    <td>{formatMoney(o.amount, o.currency)}</td>
                    <td>{formatRate(o.interest_rate)}</td>
                    <td>{o.term_months} meses</td>
                    <td>
                      <span className={`badge ${STATUS_BADGE[o.status] ?? ""}`}>
                        {OFFER_STATUS_LABELS[o.status]}
                      </span>
                    </td>
                    <td>{formatDateTime(o.created_at)}</td>
                    <td>
                      {o.status === "active" && (
                        <button
                          className="btn small danger"
                          onClick={() => handleExpire(o.id)}
                          disabled={expiringId === o.id}
                        >
                          {expiringId === o.id ? "Expirando…" : "Expirar"}
                        </button>
                      )}
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
