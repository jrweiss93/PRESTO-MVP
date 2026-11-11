import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { Notification } from "@/shared/api/types";
import { formatDateTime } from "@/shared/lib/format";
import { cn } from "@/shared/lib";

const EVENT_LABELS: Record<string, string> = {
  installment_due_soon: "Cuota por vencer",
  installment_overdue: "Cuota vencida",
  investment_settled: "Inversión liquidada",
  budget_alert: "Alerta de presupuesto",
  loan_created: "Préstamo creado",
};

const EVENT_ICONS: Record<string, string> = {
  installment_due_soon: "⚠️",
  installment_overdue: "🔴",
  investment_settled: "✅",
  budget_alert: "📊",
  loan_created: "🤝",
};

export default function Notifications() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await api.listNotifications());
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron cargar los avisos.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleReadAll() {
    try {
      await api.markAllNotificationsRead();
    } catch {
      // si falla, se reintenta al recargar
    }
    await load();
  }

  async function handleRead(id: string) {
    try {
      await api.markNotificationRead(id);
    } catch {
      // si falla, el aviso sigue sin leer
    }
    await load();
  }

  async function handleOpen(notification: Notification) {
    if (notification.read_at == null) {
      await handleRead(notification.id);
    }
    if (notification.event_type === "loan_created") {
      navigate(`/prestamos/${notification.reference_id}`);
    }
  }

  const unreadCount = items.filter((n) => n.read_at == null).length;

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1>Notificaciones</h1>
          <p className="page-subtitle">
            Avisos de tus préstamos, cuotas, inversiones y presupuestos.
          </p>
        </div>
        {unreadCount > 0 && (
          <button className="btn secondary" type="button" onClick={handleReadAll}>
            Marcar todas como leídas
          </button>
        )}
      </div>

      {error && <div className="alert error">{error}</div>}

      {loading ? (
        <div className="loading">Cargando…</div>
      ) : items.length === 0 ? (
        <div className="card">
          <p className="text-muted mb-0">Todavía no tenés avisos.</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((notification) => {
            const isUnread = notification.read_at == null;
            return (
              <li key={notification.id}>
                <button
                  type="button"
                  onClick={() => void handleOpen(notification)}
                  className={cn(
                    "flex w-full items-start gap-3 rounded-xl border p-4 text-left",
                    isUnread
                      ? "border-brand-200 bg-brand-50/60"
                      : "border-gray-200 bg-white",
                  )}
                >
                  <span className="text-lg leading-6">
                    {EVENT_ICONS[notification.event_type] ?? "🔔"}
                  </span>
                  <span className="flex-1">
                    <span
                      className={cn(
                        "block text-theme-sm",
                        isUnread
                          ? "font-semibold text-gray-900"
                          : "font-medium text-gray-700",
                      )}
                    >
                      {EVENT_LABELS[notification.event_type] ?? notification.event_type}
                    </span>
                    <span className="mt-0.5 block text-theme-xs text-gray-500">
                      {formatDateTime(notification.created_at)}
                    </span>
                    {notification.event_type === "loan_created" && (
                      <span className="mt-1 block text-theme-xs font-medium text-brand-500">
                        Ver préstamo →
                      </span>
                    )}
                  </span>
                  {isUnread && (
                    <span className="badge info">Nuevo</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}
