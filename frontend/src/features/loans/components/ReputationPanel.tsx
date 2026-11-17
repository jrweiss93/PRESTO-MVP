import { useEffect, useState } from "react";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { UserReputation } from "@/shared/api/types";
import { formatDateTime } from "@/shared/lib/format";

/**
 * Reputación recibida por un usuario. Se muestra en su perfil y agrega las
 * recomendaciones que dejaron las contrapartes de sus préstamos.
 */
export default function ReputationPanel({ userId }: { userId: string }) {
  const [data, setData] = useState<UserReputation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const reputation = await api.getUserReputation(userId);
        if (active) setData(reputation);
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "No se pudo cargar tu reputación.",
        );
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [userId]);

  if (loading) {
    return (
      <div className="card">
        <h2>Reputación</h2>
        <div className="loading">Cargando reputación…</div>
      </div>
    );
  }

  return (
    <div className="card" id="reputacion">
      <div className="section-header">
        <div>
          <h2 className="mt-0 mb-1">Reputación</h2>
          <p className="small text-muted mb-0">
            Lo que dicen las personas con las que operaste.
          </p>
        </div>
        <span className="badge info">Pública en Presto</span>
      </div>

      {error && <div className="alert error">{error}</div>}

      {!data || data.total === 0 ? (
        <div className="empty-state review-empty">
          Todavía no tenés reseñas. Cuando cierres una operación, la otra parte
          puede recomendarte y eso va a aparecer acá.
        </div>
      ) : (
        <>
          <div className="reputation-summary">
            <div className="reputation-score">
              {data.recommendation_rate.toFixed(0)}%
            </div>
            <div>
              <strong>
                {data.recommended} de {data.total}{" "}
                {data.total === 1 ? "persona te recomienda" : "personas te recomiendan"}
              </strong>
              <p className="small text-muted mb-0">
                {data.not_recommended === 0
                  ? "Sin recomendaciones negativas."
                  : `${data.not_recommended} ${
                      data.not_recommended === 1
                        ? "persona no te recomienda"
                        : "personas no te recomiendan"
                    }.`}
              </p>
            </div>
          </div>

          <ul className="reputation-list">
            {data.reviews.map((review) => (
              <li key={review.id} className="reputation-review">
                <div className="reputation-review-head">
                  <span className="small font-medium">
                    {review.reviewer_email ?? "Usuario de Presto"}
                  </span>
                  <span
                    className={`badge ${review.recommended ? "success" : "danger"}`}
                  >
                    {review.recommended ? "Recomendado" : "No recomendado"}
                  </span>
                </div>
                {review.comment && (
                  <p className="review-comment">“{review.comment}”</p>
                )}
                <span className="small text-muted">
                  {formatDateTime(review.created_at)}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
