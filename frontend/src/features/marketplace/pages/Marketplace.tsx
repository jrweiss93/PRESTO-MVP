import { useEffect, useState, type FormEvent } from "react";
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

const INITIAL_FILTERS = {
  amount_min: "",
  amount_max: "",
  currency: "" as Currency | "",
  max_rate: "",
  term_months: "",
  ordering: "" as OrderingField | "",
};

type Filters = typeof INITIAL_FILTERS;

function buildFilters(next: Filters): api.OfferFilters {
  return {
    amount_min: next.amount_min || undefined,
    amount_max: next.amount_max || undefined,
    currency: next.currency || undefined,
    max_rate: next.max_rate || undefined,
    term_months: next.term_months ? Number(next.term_months) : undefined,
    ordering: next.ordering || undefined,
  };
}

export default function Marketplace() {
  const navigate = useNavigate();
  const idempotency = useIdempotencyKey();
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState<OfferMatch[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<OfferComparison[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [searching, setSearching] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [acceptingId, setAcceptingId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const offers = await api.searchOffers({});
        if (active) setResults(offers);
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "No se pudieron cargar las ofertas.",
        );
        setResults([]);
      } finally {
        if (active) setSearching(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  async function fetchOffers(next: Filters) {
    setSearching(true);
    setError(null);
    setNotice(null);
    setComparison(null);
    setSelected([]);
    try {
      setResults(await api.searchOffers(buildFilters(next)));
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

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    setShowFilters(false);
    void fetchOffers(filters);
  }

  function handleClear() {
    setFilters(INITIAL_FILTERS);
    setShowFilters(false);
    void fetchOffers(INITIAL_FILTERS);
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

  const activeFilterCount = Object.values(filters).filter(Boolean).length;
  const offers = results ?? [];

  return (
    <>
      <div className="market-hero">
        <div>
          <span className="badge info mb-2 inline-flex">Mercado P2P</span>
          <h1 className="mt-0">Marketplace de préstamos</h1>
          <p className="page-subtitle mb-0">
            Ofertas activas de prestamistas. Compará condiciones y aceptá la que
            más te convenga.
          </p>
        </div>
        <button
          type="button"
          className="btn secondary"
          onClick={() => setShowFilters((open) => !open)}
          aria-expanded={showFilters}
        >
          {showFilters ? "Ocultar filtros" : "Filtrar ofertas"}
          {activeFilterCount > 0 && (
            <span className="badge info">{activeFilterCount}</span>
          )}
        </button>
      </div>

      {showFilters && (
        <div className="card marketplace-filters">
          <div className="marketplace-filters-head">
            <h2>Filtrar ofertas</h2>
            <p className="small text-muted mb-0">
              Ajustá el monto, la tasa o el plazo. El tablero se actualiza al
              aplicar.
            </p>
          </div>
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
            <div className="btn-row mt-4">
              <button className="btn" type="submit" disabled={searching}>
                {searching ? "Buscando…" : "Aplicar filtros"}
              </button>
              <button
                className="btn secondary"
                type="button"
                onClick={handleClear}
                disabled={searching}
              >
                Limpiar
              </button>
            </div>
          </form>
        </div>
      )}

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <section className="market-board-section">
        <div className="market-board-head">
          <div>
            <h2 className="mb-1">Ofertas en el tablero</h2>
            <p className="small text-muted mb-0">
              {results === null
                ? "Cargando ofertas…"
                : `${offers.length} ${
                    offers.length === 1 ? "oferta activa" : "ofertas activas"
                  }${searching ? " · Actualizando…" : ""}`}
            </p>
          </div>
          {selected.length > 0 && (
            <div className="compare-tray">
              <span>
                {selected.length} seleccionada
                {selected.length === 1 ? "" : "s"}
              </span>
              <div className="btn-row">
                <button
                  className="btn small"
                  type="button"
                  onClick={handleCompare}
                  disabled={selected.length < 2 || comparing}
                >
                  {comparing ? "Comparando…" : "Comparar"}
                </button>
                <button
                  className="btn secondary small"
                  type="button"
                  onClick={() => {
                    setSelected([]);
                    setComparison(null);
                  }}
                >
                  Limpiar
                </button>
              </div>
            </div>
          )}
        </div>

        {results === null ? (
          <div className="card">
            <div className="loading">Cargando ofertas…</div>
          </div>
        ) : offers.length === 0 ? (
          <div className="card">
            <div className="empty-state">
              No hay ofertas que coincidan con tu búsqueda.{" "}
              <button
                type="button"
                className="text-brand-500 hover:text-brand-600"
                onClick={handleClear}
              >
                Ver todas las ofertas
              </button>
            </div>
          </div>
        ) : (
          <div className="offer-board">
            {offers.map((offer) => {
              const isSelected = selected.includes(offer.id);
              return (
                <article
                  key={offer.id}
                  className={`offer-card${isSelected ? " selected" : ""}`}
                >
                  <div className="offer-card-top">
                    <span className="badge info">Oferta activa</span>
                    <label className="offer-compare">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(offer.id)}
                        className="size-4 accent-brand-500 p-0"
                      />
                      Comparar
                    </label>
                  </div>

                  <div className="offer-amount">
                    {formatMoney(offer.amount, offer.currency)}
                    <span className="offer-currency">{offer.currency}</span>
                  </div>

                  <div className="offer-metrics">
                    <div>
                      <span className="offer-metric-label">Tasa</span>
                      <strong>{formatRate(offer.interest_rate)}</strong>
                    </div>
                    <div>
                      <span className="offer-metric-label">Plazo</span>
                      <strong>{offer.term_months} meses</strong>
                    </div>
                  </div>

                  <div className="offer-requirements">
                    <span className="offer-metric-label">Requisitos</span>
                    <p>{offer.requirements || "Sin requisitos adicionales."}</p>
                  </div>

                  <div className="offer-card-footer">
                    <span className="offer-lender">Prestamista verificado</span>
                    <button
                      className="btn small"
                      type="button"
                      onClick={() => handleAccept(offer.id)}
                      disabled={acceptingId === offer.id}
                    >
                      {acceptingId === offer.id
                        ? "Aceptando…"
                        : "Aceptar oferta"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

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
