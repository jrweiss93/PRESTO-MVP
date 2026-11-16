import { useEffect, useRef, useState, type FormEvent } from "react";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { LoanDetail, LoanMessage } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import { formatDateTime } from "@/shared/lib/format";

/**
 * Chat privado del préstamo.
 *
 * El backend solo devuelve mensajes a las dos partes. El componente refresca
 * cada 8 segundos y al enfocar la ventana para que la conversación se sienta
 * viva durante la demo, sin necesitar WebSockets.
 */
export default function LoanChat({ loan }: { loan: LoanDetail }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState<LoanMessage[]>([]);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const isBorrower = loan.borrower_user_id === user?.id;
  const counterpartEmail = isBorrower ? loan.lender_email : loan.borrower_email;

  useEffect(() => {
    let active = true;

    const refresh = async () => {
      try {
        const data = await api.listLoanMessages(loan.id);
        if (!active) return;
        setMessages(data);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "No se pudo cargar el chat del préstamo.",
        );
      } finally {
        if (active) setLoading(false);
      }
    };

    void refresh();
    const interval = window.setInterval(refresh, 8000);
    const onFocus = () => void refresh();
    const onVisibility = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [loan.id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages.length]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const text = body.trim();
    if (!text || sending) return;
    setSending(true);
    setError(null);
    try {
      const message = await api.sendLoanMessage(loan.id, text);
      setMessages((current) =>
        current.some((item) => item.id === message.id)
          ? current
          : [...current, message],
      );
      setBody("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo enviar el mensaje.",
      );
    } finally {
      setSending(false);
    }
  }

  function senderName(message: LoanMessage) {
    if (message.sender_user_id === user?.id) return "Vos";
    return counterpartEmail ?? "La otra parte";
  }

  return (
    <div className="card loan-chat" id="chat">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="mb-1">Chat del préstamo</h2>
          <p className="small text-muted mb-0">
            Canal privado entre vos y {counterpartEmail ?? "la otra parte"}.
            Sirve para coordinar pagos y detalles de esta operación.
          </p>
        </div>
        <span className="badge success">Privado</span>
      </div>

      <div className="chat-messages" aria-live="polite">
        {loading ? (
          <div className="loading">Cargando mensajes…</div>
        ) : messages.length === 0 ? (
          <div className="empty-state chat-empty">
            Todavía no hay mensajes. Escribile a{" "}
            {counterpartEmail ?? "la otra parte"} para coordinar el préstamo.
          </div>
        ) : (
          messages.map((message) => {
            const isMine = message.sender_user_id === user?.id;
            return (
              <div
                key={message.id}
                className={`chat-bubble${isMine ? " mine" : ""}`}
              >
                <div className="chat-bubble-meta">
                  <span>{senderName(message)}</span>
                  <span>{formatDateTime(message.created_at)}</span>
                </div>
                <p>{message.body}</p>
              </div>
            );
          })
        )}
        <div ref={endRef} />
      </div>

      {error && <div className="alert error">{error}</div>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Escribí un mensaje…"
          maxLength={1000}
          aria-label="Mensaje para la otra parte"
        />
        <button
          className="btn"
          type="submit"
          disabled={sending || !body.trim()}
        >
          {sending ? "Enviando…" : "Enviar"}
        </button>
      </form>
    </div>
  );
}
