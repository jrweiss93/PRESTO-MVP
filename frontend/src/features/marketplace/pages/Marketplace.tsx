import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type {
  Currency,
  OfferComparison,
  OfferMatch,
  OrderingField,
} from "@/shared/api/types";
import { formatMoney, formatRate } from "@/shared/lib/format";
import { compareDecimals } from "@/shared/lib/decimal";
import { useIdempotencyKey } from "@/shared/lib/useIdempotencyKey";

const MAX_COMPARE = 5;

export default function Marketplace() {
  const navigate = useNavigate();
  const idempotency = useIdempotencyKey();
  const [filters, setFilters] = useState({
    amount_min: "",
    amount_max: "",
    currency: "" as Currency | "",
    max_rate: "",
    term_months: "",
    ordering: "" as OrderingField | "",
  });
  const [results, setResults] = useState<OfferMatch[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<OfferComparison[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [acceptingId, setAcceptingId] = useState<string | null>(null);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    setSearching(true);
    setError(null);
    setNotice(null);
    setComparison(null);
    setSelected([]);
    try {
      const offers = await api.searchOffers({
        amount_min: filters.amount_min || undefined,
        amount_max: filters.amount_max || undefined,
        currency: filters.currency || undefined,
        max_rate: filters.max_rate || undefined,
        term_months: filters.term_months
          ? Number(filters.term_months)
          : undefined,
        ordering: filters.ordering || undefined,
      });
      setResults(offers);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron buscar ofertas.",
      );
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  function toggleSelect(id: string) {
    setComparison(null);
    setSelected((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length >= MAX_COMPARE
          ? prev
          : [...prev, id],
    );
  }

  async function handleCompare() {
    if (selected.length < 2) return;
    setComparing(true);
    setError(null);
    try {
      setComparison(await api.compareOffers({ offer_ids: selected }));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron comparar las ofertas.",
      );
    } finally {
      setComparing(false);
    }
  }

  async function handleAccept(offerId: string) {
    setAcceptingId(offerId);
    setError(null);
    setNotice(null);
    try {
      const loan = await api.acceptOffer(
        { offer_id: offerId },
        idempotency.get(),
      );
      idempotency.reset();
      setNotice("Oferta aceptada. Préstamo creado.");
      navigate(`/prestamos/${loan.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "No se pudo aceptar la oferta.",
      );
      setAcceptingId(null);
    }
  }

  const bestComparisonId = comparison?.length
    ? comparison.reduce((best, c) =>
        compareDecimals(c.total_cost, best.total_cost) < 0 ? c : best,
      ).id
    : null;

  return (
    <>
      <h1>Marketplace de préstamos</h1>
      <p className="page-subtitle">
        Buscá ofertas activas de prestamistas, comparalas y aceptá la que más te
        convenga.
      </p>

      <div className="card">
        <h2>Filtros de búsqueda</h2>
        <form onSubmit={handleSearch}>
          <div className="form-grid">
            <label className="field">
              Monto mínimo
              <input
                type="number"
                step="0.01"
                min="0"
                value={filters.amount_min}
                onChange={(e) =>
                  setFilters({ ...filters, amount_min: e.target.value })
                }
              />
            </label>
            <label className="field">
              Monto máximo
              <input
                type="number"
                step="0.01"
                min="0"
                value={filters.amount_max}
                onChange={(e) =>
                  setFilters({ ...filters, amount_max: e.target.value })
                }
              />
            </label>
            <label className="field">
              Moneda
              <select
                value={filters.currency}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    currency: e.target.value as Currency | "",
                  })
                }
              >
                <option value="">Todas</option>
                <option value="ARS">ARS</option>
                <option value="USD">USD</option>
              </select>
            </label>
            <label className="field">
              Tasa máxima (TNA %)
              <input
                type="number"
                step="0.01"
                min="0"
                value={filters.max_rate}
                onChange={(e) =>
                  setFilters({ ...filters, max_rate: e.target.value })
                }
              />
            </label>
            <label className="field">
              Plazo (meses)
              <input
                type="number"
                min="1"
                value={filters.term_months}
                onChange={(e) =>
                  setFilters({ ...filters, term_months: e.target.value })
                }
              />
            </label>
            <label className="field">
              Ordenar por
              <select
                value={filters.ordering}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    ordering: e.target.value as OrderingField | "",
                  })
                }
              >
                <option value="">Relevancia</option>
                <option value="rate">Tasa</option>
                <option value="term">Plazo</option>
                <option value="amount">Monto</option>
              </select>
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button className="btn" type="submit" disabled={searching}>
              {searching ? "Buscando…" : "Buscar ofertas"}
            </button>
          </div>
        </form>
      </div>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      {results !== null && (
        <div className="card">
          <div className="section-header">
            <h2 className="mt-0 mb-0">Resultados ({results.length})</h2>
            {selected.length >= 2 && (
              <button
                className="btn secondary"
                onClick={handleCompare}
                disabled={comparing}
              >
                {comparing
                  ? "Comparando…"
                  : `Comparar seleccionadas (${selected.length})`}
              </button>
            )}
          </div>
          {results.length === 0 ? (
            <div className="empty-state">
              No hay ofertas que coincidan con tu búsqueda.
            </div>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th></th>
                    <th>Monto</th>
                    <th>Tasa</th>
                    <th>Plazo</th>
                    <th>Requisitos</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((o) => (
                    <tr key={o.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selected.includes(o.id)}
                          onChange={() => toggleSelect(o.id)}
                          aria-label="Seleccionar oferta para comparar"
                        />
                      </td>
                      <td>{formatMoney(o.amount, o.currency)}</td>
                      <td>{formatRate(o.interest_rate)}</td>
                      <td>{o.term_months} meses</td>
                      <td className="small">{o.requirements || "—"}</td>
                      <td>
                        <button
                          className="btn small"
                          onClick={() => handleAccept(o.id)}
                          disabled={acceptingId === o.id}
                        >
                          {acceptingId === o.id ? "Aceptando…" : "Aceptar"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {comparison && comparison.length > 0 && (
        <div className="card">
          <h2>Comparación de ofertas</h2>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Monto</th>
                  <th>Tasa</th>
                  <th>Plazo</th>
                  <th>Cuota</th>
                  <th>Interés total</th>
                  <th>Costo total</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((c) => (
                  <tr key={c.id}>
                    <td>{formatMoney(c.amount, c.currency)}</td>
                    <td>{formatRate(c.interest_rate)}</td>
                    <td>{c.term_months} meses</td>
                    <td>{formatMoney(c.installment, c.currency)}</td>
                    <td>{formatMoney(c.total_interest, c.currency)}</td>
                    <td>
                      <strong>{formatMoney(c.total_cost, c.currency)}</strong>
                    </td>
                    <td>
                      {c.id === bestComparisonId && (
                        <span className="badge success">Más barata</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
