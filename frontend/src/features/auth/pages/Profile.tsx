import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { KYCVerification } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import { KYC_STATUS_LABELS, formatDateTime } from "@/shared/lib/format";

const KYC_BADGE: Record<string, string> = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
};

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const [kyc, setKyc] = useState<KYCVerification | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [form, setForm] = useState({
    phone_number: "",
    date_of_birth: "",
    country: "",
  });
  const [savingProfile, setSavingProfile] = useState(false);

  const [docType, setDocType] = useState("dni");
  const [docNumber, setDocNumber] = useState("");
  const [requestingKyc, setRequestingKyc] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setKyc(await api.getKyc());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "No se pudo cargar el estado KYC.",
        );
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleProfile(e: FormEvent) {
    e.preventDefault();
    setSavingProfile(true);
    setError(null);
    setNotice(null);
    try {
      await api.updateMe({
        phone_number: form.phone_number || undefined,
        date_of_birth: form.date_of_birth || null,
        country: form.country || undefined,
      });
      await refreshUser().catch(() => undefined);
      setNotice("Perfil actualizado.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo actualizar el perfil.",
      );
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleKyc(e: FormEvent) {
    e.preventDefault();
    setRequestingKyc(true);
    setError(null);
    setNotice(null);
    try {
      const created = await api.requestKyc({
        documents: {
          type: docType,
          number: docNumber,
          submitted_at: new Date().toISOString(),
        },
      });
      setKyc(created);
      setNotice("Solicitud de verificación KYC enviada.");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "No se pudo solicitar el KYC.",
      );
    } finally {
      setRequestingKyc(false);
    }
  }

  return (
    <>
      <h1>Perfil y KYC</h1>
      <p className="page-subtitle">
        Datos de tu cuenta y verificación de identidad.
      </p>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <div className="card">
        <h2>Cuenta</h2>
        <p className="mt-0 mb-0">
          <strong>Email:</strong> {user?.email}
          {user?.first_name && (
            <>
              <br />
              <strong>Nombre:</strong> {user.first_name} {user.last_name}
            </>
          )}
          <br />
          <strong>ID:</strong> <span className="mono">{user?.id}</span>
        </p>
      </div>

      <div className="card">
        <h2>Datos adicionales</h2>
        <form onSubmit={handleProfile}>
          <div className="form-grid">
            <label className="field">
              Teléfono
              <input
                type="text"
                maxLength={32}
                value={form.phone_number}
                onChange={(e) =>
                  setForm({ ...form, phone_number: e.target.value })
                }
              />
            </label>
            <label className="field">
              Fecha de nacimiento
              <input
                type="date"
                value={form.date_of_birth}
                onChange={(e) =>
                  setForm({ ...form, date_of_birth: e.target.value })
                }
              />
            </label>
            <label className="field">
              País (código ISO, ej. AR)
              <input
                type="text"
                maxLength={2}
                pattern="[A-Z]{2}"
                title="Dos letras mayúsculas (ISO 3166-1)"
                value={form.country}
                onChange={(e) =>
                  setForm({ ...form, country: e.target.value.toUpperCase() })
                }
                placeholder="AR"
              />
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button className="btn" type="submit" disabled={savingProfile}>
              {savingProfile ? "Guardando…" : "Guardar cambios"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Verificación KYC</h2>
        {loading ? (
          <div className="loading">Cargando…</div>
        ) : kyc ? (
          <>
            <p>
              Estado:{" "}
              <span className={`badge ${KYC_BADGE[kyc.status] ?? ""}`}>
                {KYC_STATUS_LABELS[kyc.status]}
              </span>
            </p>
            <p className="small text-muted mb-0">
              Solicitada {formatDateTime(kyc.requested_at)}
              {kyc.resolved_at &&
                ` · Resuelta ${formatDateTime(kyc.resolved_at)}`}
            </p>
            {kyc.status === "rejected" && (
              <p className="small">
                Tu solicitud fue rechazada. Podés volver a solicitarla con
                documentación actualizada.
              </p>
            )}
          </>
        ) : (
          <form onSubmit={handleKyc}>
            <p className="small text-muted">
              Necesitás completar la verificación de identidad para operar en la
              plataforma.
            </p>
            <div className="form-grid">
              <label className="field">
                Tipo de documento
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                >
                  <option value="dni">DNI</option>
                  <option value="passport">Pasaporte</option>
                  <option value="national_id">Cédula de identidad</option>
                </select>
              </label>
              <label className="field">
                Número de documento
                <input
                  type="text"
                  value={docNumber}
                  onChange={(e) => setDocNumber(e.target.value)}
                  required
                />
              </label>
            </div>
            <div className="btn-row" style={{ marginTop: "0.9rem" }}>
              <button className="btn" type="submit" disabled={requestingKyc}>
                {requestingKyc ? "Enviando…" : "Solicitar verificación"}
              </button>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
