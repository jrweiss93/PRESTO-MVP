import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { InvestmentProduct, Position } from "@/shared/api/types";
import {
  POSITION_STATUS_LABELS,
  formatDate,
  formatDateTime,
  formatMoney,
  formatRate,
} from "@/shared/lib/format";
import { sumDecimals } from "@/shared/lib/decimal";
import { ENABLE_ASSISTANT } from "@/shared/lib/features";
import { useIdempotencyKey } from "@/shared/lib/useIdempotencyKey";

export default function Investments() {
  const [products, setProducts] = useState<InvestmentProduct[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const idempotency = useIdempotencyKey();

  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [prod, pos] = await Promise.all([
        api.listProducts(),
        api.listPositions(),
      ]);
      setProducts(prod);
      setPositions(pos);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron cargar las inversiones.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleOpen(e: FormEvent) {
    e.preventDefault();
    const product = products.find((p) => p.id === selectedProduct);
    if (!product) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      await api.openPosition(
        {
          product_id: product.id,
          amount,
          currency: product.currency,
        },
        idempotency.get(),
      );
      idempotency.reset();
      setNotice("Posición de inversión abierta.");
      setAmount("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo abrir la inversión.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="loading">Cargando inversiones…</div>;

  const activePositions = positions.filter((p) => p.status === "active");
  const totalInvested = sumDecimals(activePositions.map((p) => p.amount));

  return (
    <>
      <h1>Inversiones</h1>
      <p className="page-subtitle">
        Productos de inversión y tus posiciones abiertas.
      </p>

      <div className="alert warning">
        <strong>Modo demostración.</strong> Estos productos están sujetos a
        autorización regulatoria (CNV / BCRA) y hoy no constituyen una oferta
        pública de inversión. Ofrecer al público instrumentos para financiar
        créditos requiere autorización de la CNV o un vehículo autorizado.{" "}
        {ENABLE_ASSISTANT ? (
          <>
            Más info en <Link to="/asistente">Presti → Marco legal</Link>.
          </>
        ) : (
          <>Más info en el documento regulatorio del proyecto.</>
        )}
      </div>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <div className="card-grid">
        <div className="stat-card">
          <div className="label">Posiciones activas</div>
          <div className="value">{activePositions.length}</div>
        </div>
        <div className="stat-card">
          <div className="label">Capital invertido</div>
          <div className="value">{formatMoney(totalInvested)}</div>
        </div>
      </div>

      <div className="card">
        <h2>Productos disponibles</h2>
        {products.length === 0 ? (
          <div className="empty-state">
            No hay productos de inversión activos.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Moneda</th>
                  <th>Plazo</th>
                  <th>TNA</th>
                  <th>Mínimo</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td>Plazo fijo</td>
                    <td>{p.currency}</td>
                    <td>{p.term_days} días</td>
                    <td>{formatRate(p.annual_rate_tna)}</td>
                    <td>{formatMoney(p.min_amount, p.currency)}</td>
                    <td>
                      <span
                        className={`badge ${p.status === "active" ? "success" : "warning"}`}
                      >
                        {p.status === "active"
                          ? "Activo"
                          : p.status === "matured"
                            ? "Vencido"
                            : "Cancelado"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Abrir inversión a plazo fijo</h2>
        <form onSubmit={handleOpen}>
          <div className="form-grid">
            <label className="field">
              Producto
              <select
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
                required
              >
                <option value="">Seleccionar…</option>
                {products
                  .filter((p) => p.status === "active")
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.currency} · {p.term_days} días · TNA{" "}
                      {p.annual_rate_tna}% · mín.{" "}
                      {formatMoney(p.min_amount, p.currency)}
                    </option>
                  ))}
              </select>
            </label>
            <label className="field">
              Monto a invertir
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button
              className="btn"
              type="submit"
              disabled={submitting || !selectedProduct}
            >
              {submitting ? "Abriendo…" : "Invertir"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Mis posiciones</h2>
        {positions.length === 0 ? (
          <div className="empty-state">Todavía no abriste inversiones.</div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Monto</th>
                  <th>Interés estimado</th>
                  <th>Apertura</th>
                  <th>Vencimiento</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((p) => (
                  <tr key={p.id}>
                    <td>{formatMoney(p.amount)}</td>
                    <td>{formatMoney(p.interest_amount)}</td>
                    <td>{formatDateTime(p.opened_at)}</td>
                    <td>{formatDate(p.maturity_date)}</td>
                    <td>
                      <span
                        className={`badge ${p.status === "active" ? "info" : "success"}`}
                      >
                        {POSITION_STATUS_LABELS[p.status]}
                      </span>
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
