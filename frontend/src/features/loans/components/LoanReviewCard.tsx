import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { Loan, LoanReviewStatus } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import { CheckCircleIcon, CloseIcon } from "@/shared/ui/icons";
import { formatDate, formatDateTime, formatMoney } from "@/shared/lib/format";

/**
 * Tarjeta para que una parte recomiende (o no) a la otra después de una
 * operación. Se usa en el dashboard y en el detalle del préstamo.
 */
export default function LoanReviewCard({
  loan,
  refreshKey = 0,
  onReviewed,
}: {
  loan: Loan;
  refreshKey?: number;
  onReviewed?: () => void;
}) {
  const { user } = useAuth();
  const [status, setStatus] = useState<LoanReviewStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [choice, setChoice] = useState<boolean | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const isBorrower = loan.borrower_user_id === user?.id;
  const counterpartEmail = isBorrower
    ? loan.lender_email
    : loan.borrower_email;

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await api.getLoanReview(loan.id);
        if (active) setStatus(data);
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "No se pudo cargar la reputación de la operación.",
        );
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [loan.id, refreshKey]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (choice === null) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      await api.createLoanReview(loan.id, {
        recommended: choice,
        comment: comment.trim(),
      });
      const refreshed = await api.getLoanReview(loan.id);
      setStatus(refreshed);
      setNotice("Opinión publicada. Ya forma parte de la reputación.");
      setChoice(null);
      setComment("");
      onReviewed?.();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo publicar la opinión.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const myReview = status?.my_review;
  const reputation = status?.counterpart_reputation;
  const hasReputation = Boolean(reputation && reputation.total > 0);
  const rate = reputation?.recommendation_rate ?? 0;
  const counterpartLabel = counterpartEmail ?? "la otra parte";

  return (
    <section className="review-item">
      <div className="review-item-head">
        <div>
          <span className="review-eyebrow">Tu opinión</span>
          <h3 className="review-title">{counterpartLabel}</h3>
          <p className="small text-muted mb-0">
            Operación de {formatMoney(loan.principal, loan.currency)} ·{" "}
            {formatDate(loan.accepted_at)}
          </p>
        </div>
        <span
          className={`review-rate-pill${hasReputation ? "" : " muted"}`}
          title={
            hasReputation
              ? `${reputation?.recommended} de ${reputation?.total} reseñas recomiendan a esta persona`
              : "Todavía no tiene reseñas"
          }
        >
          {hasReputation ? `${rate.toFixed(0)}%` : "Sin reseñas"}
        </span>
      </div>

      {loading ? (
        <div className="loading review-loading">Cargando reputación…</div>
      ) : myReview ? (
        <div className="review-done">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`badge ${myReview.recommended ? "success" : "danger"}`}
            >
              {myReview.recommended
                ? "Lo recomendás"
                : "No lo recomendás"}
            </span>
            <span className="small text-muted">
              Registrada {formatDateTime(myReview.created_at)}
            </span>
          </div>
          {myReview.comment && (
            <p className="review-comment">“{myReview.comment}”</p>
          )}
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="review-form">
          <p className="small text-muted mb-2">
            ¿Recomendás a {counterpartLabel} después de esta operación?
          </p>
          <div className="review-actions">
            <button
              type="button"
              className={`review-choice${choice === true ? " selected" : ""}`}
              onClick={() => setChoice(true)}
              aria-pressed={choice === true}
            >
              <CheckCircleIcon className="size-4" />
              Recomiendo
            </button>
            <button
              type="button"
              className={`review-choice negative${choice === false ? " selected" : ""}`}
              onClick={() => setChoice(false)}
              aria-pressed={choice === false}
            >
              <CloseIcon className="size-4" />
              No recomiendo
            </button>
          </div>
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Comentario opcional (máximo 500 caracteres)"
            maxLength={500}
            rows={2}
            aria-label="Comentario de la opinión"
          />
          <div className="review-form-footer">
            <span className="small text-muted">
              Se muestra en el perfil de {counterpartLabel}.
            </span>
            <button
              className="btn small"
              type="submit"
              disabled={submitting || choice === null}
            >
              {submitting ? "Publicando…" : "Publicar opinión"}
            </button>
          </div>
        </form>
      )}

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}
    </section>
  );
}
