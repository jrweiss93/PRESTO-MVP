import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import { useAuth } from "@/features/auth/AuthContext";
import { useIdempotencyKey } from "@/shared/lib/useIdempotencyKey";
import type {
  Account,
  CreateTransactionType,
  Currency,
  LedgerTransaction,
  Loan,
} from "@/shared/api/types";
import {
  TX_TYPE_LABELS,
  formatDateTime,
  formatMoney,
} from "@/shared/lib/format";

const TX_TYPES: CreateTransactionType[] = ["deposit", "withdrawal", "transfer"];

export default function Wallet() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<LedgerTransaction[]>([]);
  const [hasActiveLoan, setHasActiveLoan] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [newCurrency, setNewCurrency] = useState<Currency>("ARS");
  const [creatingAccount, setCreatingAccount] = useState(false);

  const idempotency = useIdempotencyKey();
  const [txType, setTxType] = useState<CreateTransactionType>("deposit");
  const [txCurrency, setTxCurrency] = useState<Currency>("ARS");
  const [txAmount, setTxAmount] = useState("");
  const [txDestination, setTxDestination] = useState("");
  const [txDescription, setTxDescription] = useState("");
  const [submittingTx, setSubmittingTx] = useState(false);

  const load = useCallback(async () => {
    try {
      const [acc, txs, loans] = await Promise.all([
        api.listAccounts(),
        api.listTransactions().catch(() => [] as LedgerTransaction[]),
        api.listLoans().catch(() => [] as Loan[]),
      ]);
      setAccounts(acc);
      setTransactions(txs);
      setHasActiveLoan(
        loans.some(
          (loan) =>
            loan.borrower_user_id === user?.id &&
            (loan.status === "active" || loan.status === "defaulted"),
        ),
      );
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo cargar la billetera.",
      );
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (hasActiveLoan && txType === "withdrawal") setTxType("deposit");
  }, [hasActiveLoan, txType]);

  async function handleCreateAccount(e: FormEvent) {
    e.preventDefault();
    setCreatingAccount(true);
    setError(null);
    setNotice(null);
    try {
      await api.createAccount({ currency: newCurrency });
      setNotice(`Billetera en ${newCurrency} creada.`);
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo crear la billetera.",
      );
    } finally {
      setCreatingAccount(false);
    }
  }

  async function handleTransaction(e: FormEvent) {
    e.preventDefault();
    setSubmittingTx(true);
    setError(null);
    setNotice(null);
    try {
      await api.createTransaction(
        {
          type: txType,
          currency: txCurrency,
          amount: txAmount,
          destination_account_id: txType === "transfer" ? txDestination : null,
          description: txDescription || undefined,
        },
        idempotency.get(),
      );
      idempotency.reset();
      setNotice("Movimiento registrado.");
      setTxAmount("");
      setTxDestination("");
      setTxDescription("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo registrar el movimiento.",
      );
    } finally {
      setSubmittingTx(false);
    }
  }

  const otherAccounts = accounts.filter((a) => a.currency === txCurrency);
  const transactionTypes = hasActiveLoan
    ? TX_TYPES.filter((type) => type !== "withdrawal")
    : TX_TYPES;

  if (loading) return <div className="loading">Cargando billetera…</div>;

  return (
    <>
      <h1>Billetera</h1>
      <p className="page-subtitle">
        Cuentas, saldos y movimientos de dinero (depósitos, retiros y
        transferencias).
      </p>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}
      {hasActiveLoan && (
        <div className="alert warning">
          Tenés un préstamo vigente: podés depositar y pagar cuotas, pero no
          retirar hasta terminarlo o cancelarlo.{" "}
          <Link to="/prestamos">Ver mis préstamos</Link>
        </div>
      )}

      <div className="card-grid">
        {accounts.length === 0 && (
          <div className="stat-card">
            <div className="label">Sin billeteras</div>
            <div className="small text-muted">
              Creá una billetera para empezar a operar.
            </div>
          </div>
        )}
        {accounts.map((acc) => (
          <div className="stat-card" key={acc.id}>
            <div className="label">
              {acc.currency} · {acc.kind}
            </div>
            <div className="value">
              {formatMoney(acc.balance, acc.currency)}
            </div>
            <div className="small text-muted">
              Creada {formatDateTime(acc.created_at)}
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Crear billetera</h2>
        <form className="btn-row" onSubmit={handleCreateAccount}>
          <label className="field" style={{ maxWidth: 180 }}>
            Moneda
            <select
              value={newCurrency}
              onChange={(e) => setNewCurrency(e.target.value as Currency)}
            >
              <option value="ARS">Peso argentino (ARS)</option>
              <option value="USD">Dólar (USD)</option>
            </select>
          </label>
          <button className="btn" type="submit" disabled={creatingAccount}>
            {creatingAccount ? "Creando…" : "Crear"}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Nuevo movimiento</h2>
        <form onSubmit={handleTransaction}>
          <div className="form-grid">
            <label className="field">
              Tipo
              <select
                value={txType}
                onChange={(e) =>
                  setTxType(e.target.value as CreateTransactionType)
                }
              >
                {transactionTypes.map((t) => (
                  <option key={t} value={t}>
                    {TX_TYPE_LABELS[t]}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Moneda
              <select
                value={txCurrency}
                onChange={(e) => setTxCurrency(e.target.value as Currency)}
              >
                <option value="ARS">ARS</option>
                <option value="USD">USD</option>
              </select>
            </label>
            <label className="field">
              Importe
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={txAmount}
                onChange={(e) => setTxAmount(e.target.value)}
                required
              />
            </label>
            {txType === "transfer" && (
              <label className="field">
                Cuenta destino
                <select
                  value={txDestination}
                  onChange={(e) => setTxDestination(e.target.value)}
                  required
                >
                  <option value="">Seleccionar…</option>
                  {otherAccounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.currency} — {formatMoney(a.balance, a.currency)}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="field full">
              Descripción
              <input
                type="text"
                maxLength={255}
                value={txDescription}
                onChange={(e) => setTxDescription(e.target.value)}
                placeholder="Opcional"
              />
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button className="btn" type="submit" disabled={submittingTx}>
              {submittingTx ? "Enviando…" : "Registrar movimiento"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Movimientos</h2>
        {transactions.length === 0 ? (
          <div className="empty-state">Todavía no hay movimientos.</div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Descripción</th>
                  <th>Fecha</th>
                  <th>ID</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td>
                      <span className="badge info">
                        {TX_TYPE_LABELS[tx.type] ?? tx.type}
                      </span>
                    </td>
                    <td>{tx.description || "—"}</td>
                    <td>{formatDateTime(tx.occurred_at)}</td>
                    <td className="mono">{tx.id.slice(0, 8)}…</td>
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
