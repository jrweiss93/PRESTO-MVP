import { useEffect, useState } from "react";
import { newIdempotencyKey } from "@/shared/api/client";
import * as api from "@/shared/api/endpoints";
import type {
  Account,
  CreatePayment,
  Currency,
  Payment,
  PaymentDirection,
} from "@/shared/api/types";
import {
  currencyLabel,
  formatDateTime,
  formatMoney,
} from "@/shared/lib/format";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  confirmed: "Confirmado",
  failed: "Fallido",
  reversed: "Revertido",
};

const DIRECTION_LABELS: Record<PaymentDirection, string> = {
  deposit: "Depositar",
  withdrawal: "Retirar",
  transfer: "Transferir a otro usuario",
};

export default function Payments() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState<Currency>("ARS");
  const [direction, setDirection] = useState<PaymentDirection>("transfer");
  const [destinationUser, setDestinationUser] = useState("");
  const [destinationAccount, setDestinationAccount] = useState("");
  const [sending, setSending] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [payList, accList] = await Promise.all([
        api.listPayments(),
        api.listAccounts(),
      ]);
      setPayments(payList);
      setAccounts(accList);
      if (accList.length > 0) setCurrency(accList[0].currency);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No se pudieron cargar los pagos",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSending(true);
    setFeedback(null);
    setError(null);
    try {
      const payload: CreatePayment = {
        direction,
        amount,
        currency,
        destination_user_id:
          direction === "transfer" ? destinationUser.trim() : undefined,
        destination_account:
          direction === "withdrawal" ? destinationAccount.trim() : undefined,
      };
      // La operación mueve dinero: el backend exige `Idempotency-Key`.
      await api.createPayment(payload, newIdempotencyKey());
      setFeedback("Pago registrado.");
      setAmount("");
      setDestinationUser("");
      setDestinationAccount("");
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No se pudo registrar el pago",
      );
    } finally {
      setSending(false);
    }
  }

  const currencies: Currency[] =
    accounts.length > 0
      ? Array.from(new Set(accounts.map((a) => a.currency)))
      : ["ARS", "USD"];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-title-sm font-semibold text-gray-800">Pagos</h1>
        <p className="mt-1 text-sm text-gray-500">
          Depósitos, retiros y transferencias entre usuarios de Presto.
        </p>
      </header>

      <section className="rounded-2xl border border-gray-200 bg-white p-5">
        <h2 className="text-base font-semibold text-gray-800">Nuevo pago</h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={submit}>
          <label className="flex flex-col gap-1 text-sm text-gray-600">
            Dirección
            <select
              className="rounded-lg border border-gray-300 px-3 py-2"
              value={direction}
              onChange={(e) => setDirection(e.target.value as PaymentDirection)}
            >
              {(Object.keys(DIRECTION_LABELS) as PaymentDirection[]).map(
                (d) => (
                  <option key={d} value={d}>
                    {DIRECTION_LABELS[d]}
                  </option>
                ),
              )}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm text-gray-600">
            Monto
            <input
              className="rounded-lg border border-gray-300 px-3 py-2"
              inputMode="decimal"
              placeholder="1000.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-gray-600">
            Moneda
            <select
              className="rounded-lg border border-gray-300 px-3 py-2"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as Currency)}
            >
              {currencies.map((c) => (
                <option key={c} value={c}>
                  {currencyLabel(c)}
                </option>
              ))}
            </select>
          </label>
          {direction === "transfer" && (
            <label className="flex flex-col gap-1 text-sm text-gray-600">
              Usuario destino (id)
              <input
                className="rounded-lg border border-gray-300 px-3 py-2"
                placeholder="uuid del usuario"
                value={destinationUser}
                onChange={(e) => setDestinationUser(e.target.value)}
                required
              />
            </label>
          )}
          {direction === "withdrawal" && (
            <label className="flex flex-col gap-1 text-sm text-gray-600">
              Cuenta externa de destino
              <input
                className="rounded-lg border border-gray-300 px-3 py-2"
                placeholder="CBU o alias"
                value={destinationAccount}
                onChange={(e) => setDestinationAccount(e.target.value)}
              />
            </label>
          )}
          <div className="sm:col-span-2">
            <button
              className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
              disabled={sending || amount === ""}
              type="submit"
            >
              {sending ? "Enviando…" : "Confirmar pago"}
            </button>
          </div>
        </form>
        {feedback && (
          <p className="mt-3 text-sm text-emerald-600">{feedback}</p>
        )}
      </section>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </p>
      )}

      <section className="rounded-2xl border border-gray-200 bg-white p-5">
        <h2 className="text-base font-semibold text-gray-800">Historial</h2>
        {loading ? (
          <p className="mt-3 text-sm text-gray-500">Cargando…</p>
        ) : payments.length === 0 ? (
          <p className="mt-3 text-sm text-gray-500">Todavía no hay pagos.</p>
        ) : (
          <ul className="mt-3 divide-y divide-gray-100">
            {payments.map((payment) => (
              <li
                key={payment.id}
                className="flex flex-wrap items-center justify-between gap-2 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {formatMoney(payment.amount, payment.currency)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {DIRECTION_LABELS[payment.direction] ?? payment.direction} ·{" "}
                    {formatDateTime(payment.created_at)}
                  </p>
                </div>
                <span className="text-xs text-gray-500">
                  {STATUS_LABELS[payment.status] ?? payment.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
