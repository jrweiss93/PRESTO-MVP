import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type { BackupAccount, KYCVerification } from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import {
  KYC_STATUS_LABELS,
  formatDateTime,
  formatMoney,
} from "@/shared/lib/format";

const PROVIDERS = [
  { value: "bank", label: "Banco" },
  { value: "wallet", label: "Billetera virtual" },
  { value: "mercado_pago", label: "Mercado Pago" },
  { value: "binance", label: "Binance" },
  { value: "other", label: "Otra" },
];

const BACKUP_STATUS_BADGE: Record<string, string> = {
  pending: "warning",
  verified: "success",
  rejected: "danger",
};

function providerLabel(value: string) {
  return PROVIDERS.find((provider) => provider.value === value)?.label ?? value;
}

const KYC_BADGE: Record<string, string> = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
};

export default function Profile() {
  const { user, refreshUser, logout } = useAuth();
  const [kyc, setKyc] = useState<KYCVerification | null>(null);
  const [backupAccounts, setBackupAccounts] = useState<BackupAccount[]>([]);
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
  const [resending, setResending] = useState(false);

  const [simulateMismatch, setSimulateMismatch] = useState(false);
  const [runningBiometric, setRunningBiometric] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const [backupForm, setBackupForm] = useState({
    provider: "bank",
    display_name: "",
    account_ref: "",
    currency: "ARS",
    declared_balance: "",
  });
  const [backupCodes, setBackupCodes] = useState<Record<string, string>>({});
  const [backupBusy, setBackupBusy] = useState(false);
  const [closingAccount, setClosingAccount] = useState(false);

  async function loadBackupAccounts() {
    try {
      setBackupAccounts(await api.listBackupAccounts());
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron cargar las cuentas de respaldo.",
      );
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const [verification, accounts] = await Promise.all([
          api.getKyc().catch(() => null),
          api.listBackupAccounts().catch(() => [] as BackupAccount[]),
        ]);
        setKyc(verification);
        setBackupAccounts(accounts);
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

  async function handleResendVerification() {
    setResending(true);
    setError(null);
    setNotice(null);
    try {
      const res = await api.resendEmailVerification();
      setNotice(res.detail);
      await refreshUser().catch(() => undefined);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo reenviar el correo de verificación.",
      );
    } finally {
      setResending(false);
    }
  }

  async function handleBiometric() {
    if (!kyc) return;
    setRunningBiometric(true);
    setError(null);
    setNotice(null);
    try {
      const check = await api.runBiometricCheck(kyc.id, {
        gesture: "blink",
        ...(simulateMismatch ? { mismatch: true } : {}),
      });
      setKyc(await api.getKyc());
      await refreshUser().catch(() => undefined);
      setNotice(
        check.status === "passed"
          ? "Validación biométrica aprobada (simulación). En la demo, tu identidad se verifica automáticamente."
          : "Validación biométrica rechazada (simulación de no coincidencia).",
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo ejecutar la validación biométrica.",
      );
    } finally {
      setRunningBiometric(false);
    }
  }

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    if (newPassword !== confirmPassword) {
      setError("La contraseña nueva y la confirmación no coinciden.");
      return;
    }
    setChangingPassword(true);
    try {
      const res = await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setNotice(`${res.detail} Vas a tener que volver a iniciar sesión.`);
      await logout();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo cambiar la contraseña.",
      );
    } finally {
      setChangingPassword(false);
    }
  }

  async function handleCreateBackup(e: FormEvent) {
    e.preventDefault();
    setBackupBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await api.createBackupAccount({
        provider: backupForm.provider,
        display_name: backupForm.display_name,
        account_ref: backupForm.account_ref,
        currency: backupForm.currency,
        declared_balance: backupForm.declared_balance || "0",
      });
      setBackupForm({
        provider: "bank",
        display_name: "",
        account_ref: "",
        currency: "ARS",
        declared_balance: "",
      });
      await loadBackupAccounts();
      setNotice(
        created.verification_hint
          ? `Cuenta vinculada. ${created.verification_hint}`
          : "Cuenta vinculada. Verificala para usarla como respaldo.",
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo vincular la cuenta de respaldo.",
      );
    } finally {
      setBackupBusy(false);
    }
  }

  async function handleVerifyBackup(accountId: string) {
    const code = backupCodes[accountId]?.trim();
    if (!code) {
      setError("Ingresá el código de verificación.");
      return;
    }
    setBackupBusy(true);
    setError(null);
    setNotice(null);
    try {
      await api.verifyBackupAccount(accountId, code);
      setBackupCodes((current) => ({ ...current, [accountId]: "" }));
      await loadBackupAccounts();
      setNotice("Cuenta de respaldo verificada.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo verificar la cuenta de respaldo.",
      );
    } finally {
      setBackupBusy(false);
    }
  }

  async function handleDeleteBackup(accountId: string) {
    if (!window.confirm("¿Desvincular esta cuenta de respaldo?")) return;
    setBackupBusy(true);
    setError(null);
    setNotice(null);
    try {
      await api.deleteBackupAccount(accountId);
      await loadBackupAccounts();
      setNotice("Cuenta de respaldo desvinculada.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo desvincular la cuenta de respaldo.",
      );
    } finally {
      setBackupBusy(false);
    }
  }

  async function handleCloseAccount() {
    if (
      !window.confirm(
        "¿Cerrar tu cuenta? No vas a poder volver a ingresar con este email.",
      )
    ) {
      return;
    }
    setClosingAccount(true);
    setError(null);
    setNotice(null);
    try {
      await api.closeAccount();
      await logout();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo cerrar la cuenta.",
      );
    } finally {
      setClosingAccount(false);
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
          <strong>Email:</strong> {user?.email}{" "}
          {user?.email_verified ? (
            <span className="badge success">Verificado</span>
          ) : (
            <span className="badge warning">Sin verificar</span>
          )}
          {user?.first_name && (
            <>
              <br />
              <strong>Nombre:</strong> {user.first_name} {user.last_name}
            </>
          )}
          <br />
          <strong>ID:</strong> <span className="mono">{user?.id}</span>
        </p>
        {!user?.email_verified && (
          <div style={{ marginTop: "0.9rem" }}>
            <p className="small text-muted">
              Confirmá tu email para recibir los avisos de cuotas, inversiones y
              movimientos.
            </p>
            <button
              className="btn"
              type="button"
              onClick={handleResendVerification}
              disabled={resending}
            >
              {resending ? "Enviando…" : "Reenviar correo de verificación"}
            </button>
          </div>
        )}
      </div>

      <div className="card" id="respaldo">
        <h2>Cuentas de respaldo</h2>
        <p className="small text-muted mt-0">
          Para aceptar un préstamo necesitás al menos una cuenta verificada. La
          verificación de la demo es simulada: no se consulta ni debita dinero
          real. Solo guardamos proveedor, referencia enmascarada y saldo
          informado; nunca claves ni tokens.
        </p>

        {backupAccounts.length === 0 ? (
          <div className="empty-state">
            Todavía no vinculaste ninguna cuenta de respaldo.
          </div>
        ) : (
          <div className="space-y-3">
            {backupAccounts.map((account) => (
              <div
                key={account.id}
                className="rounded-xl border border-gray-200 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <strong>{account.display_name}</strong>{" "}
                    <span className="small text-muted">
                      {providerLabel(account.provider)} · {account.masked_ref} ·{" "}
                      {account.currency}
                    </span>
                  </div>
                  <span
                    className={`badge ${BACKUP_STATUS_BADGE[account.status] ?? "info"}`}
                  >
                    {account.status === "verified"
                      ? "Verificada"
                      : account.status === "pending"
                        ? "Pendiente"
                        : "Rechazada"}
                  </span>
                </div>
                <div className="small text-muted mt-1">
                  Saldo informado:{" "}
                  {formatMoney(account.declared_balance, account.currency)}
                  {account.verified_at
                    ? ` · Verificada ${formatDateTime(account.verified_at)}`
                    : ""}
                </div>

                {account.status === "pending" && (
                  <div className="mt-3 flex flex-wrap items-end gap-2">
                    <label className="field mb-0">
                      Código de verificación
                      <input
                        type="text"
                        value={backupCodes[account.id] ?? ""}
                        onChange={(event) =>
                          setBackupCodes((current) => ({
                            ...current,
                            [account.id]: event.target.value,
                          }))
                        }
                        placeholder="123456"
                      />
                    </label>
                    <button
                      type="button"
                      className="btn"
                      onClick={() => handleVerifyBackup(account.id)}
                      disabled={backupBusy}
                    >
                      Verificar
                    </button>
                    {account.verification_hint && (
                      <span className="small text-muted">
                        {account.verification_hint}
                      </span>
                    )}
                  </div>
                )}

                <div className="mt-3">
                  <button
                    type="button"
                    className="btn secondary"
                    onClick={() => handleDeleteBackup(account.id)}
                    disabled={backupBusy}
                  >
                    Desvincular
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleCreateBackup} className="mt-4">
          <div className="form-grid">
            <label className="field">
              Proveedor
              <select
                value={backupForm.provider}
                onChange={(event) =>
                  setBackupForm({ ...backupForm, provider: event.target.value })
                }
              >
                {PROVIDERS.map((provider) => (
                  <option key={provider.value} value={provider.value}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Nombre de la cuenta
              <input
                type="text"
                value={backupForm.display_name}
                onChange={(event) =>
                  setBackupForm({
                    ...backupForm,
                    display_name: event.target.value,
                  })
                }
                placeholder="Ej. Banco Galicia"
                required
              />
            </label>
            <label className="field">
              Referencia (CBU/CVU/alias/email)
              <input
                type="text"
                value={backupForm.account_ref}
                onChange={(event) =>
                  setBackupForm({
                    ...backupForm,
                    account_ref: event.target.value,
                  })
                }
                placeholder="Se muestra enmascarada"
                required
              />
            </label>
            <label className="field">
              Moneda
              <select
                value={backupForm.currency}
                onChange={(event) =>
                  setBackupForm({ ...backupForm, currency: event.target.value })
                }
              >
                <option value="ARS">ARS</option>
                <option value="USD">USD</option>
              </select>
            </label>
            <label className="field">
              Saldo informado
              <input
                type="number"
                min="0"
                step="0.01"
                value={backupForm.declared_balance}
                onChange={(event) =>
                  setBackupForm({
                    ...backupForm,
                    declared_balance: event.target.value,
                  })
                }
                placeholder="Ej. 50000"
                required
              />
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button className="btn" type="submit" disabled={backupBusy}>
              {backupBusy ? "Guardando…" : "Vincular cuenta"}
            </button>
          </div>
        </form>
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

      {kyc && (
        <div className="card">
          <h2>Validación biométrica</h2>
          <p className="small text-muted">
            Simula una prueba de vida (selfie en vivo) y la comparación del
            rostro contra tu documento. <strong>No se procesan datos
            biométricos reales</strong>: los puntajes son simulados.
          </p>
          {kyc.biometric ? (
            <p className="mb-0">
              Última validación:{" "}
              <span
                className={`badge ${
                  kyc.biometric.status === "passed" ? "success" : "danger"
                }`}
              >
                {kyc.biometric.status === "passed" ? "Aprobada" : "Rechazada"}
              </span>
              <br />
              <span className="small text-muted">
                Prueba de vida{" "}
                {kyc.biometric.liveness_score != null
                  ? `${(Number(kyc.biometric.liveness_score) * 100).toFixed(0)}%`
                  : "—"}{" "}
                · Coincidencia{" "}
                {kyc.biometric.match_score != null
                  ? `${(Number(kyc.biometric.match_score) * 100).toFixed(0)}%`
                  : "—"}
              </span>
            </p>
          ) : (
            <p className="small text-muted">
              Todavía no se realizó la validación biométrica.
            </p>
          )}
          <label className="field">
            <span className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={simulateMismatch}
                onChange={(e) => setSimulateMismatch(e.target.checked)}
              />
              Simular que el rostro no coincide (para ver el rechazo)
            </span>
          </label>
          <div className="btn-row" style={{ marginTop: "0.6rem" }}>
            <button
              className="btn"
              type="button"
              onClick={handleBiometric}
              disabled={runningBiometric}
            >
              {runningBiometric
                ? "Validando…"
                : "Simular validación biométrica"}
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Seguridad</h2>
        <p className="small text-muted">
          Cambiá tu contraseña. Al hacerlo se cierran las otras sesiones.
        </p>
        <form onSubmit={handleChangePassword}>
          <div className="form-grid">
            <label className="field">
              Contraseña actual
              <input
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </label>
            <label className="field">
              Contraseña nueva
              <input
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                placeholder="Mínimo 8 caracteres"
              />
            </label>
            <label className="field">
              Repetir contraseña nueva
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button className="btn" type="submit" disabled={changingPassword}>
              {changingPassword ? "Guardando…" : "Cambiar contraseña"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Cerrar cuenta</h2>
        <p className="small text-muted">
          La baja es lógica: se conserva el historial financiero por auditoría.
          No se puede cerrar la cuenta con préstamos activos, en mora o
          inversiones abiertas.
        </p>
        <button
          type="button"
          className="btn secondary"
          onClick={handleCloseAccount}
          disabled={closingAccount}
        >
          {closingAccount ? "Cerrando…" : "Cerrar mi cuenta"}
        </button>
      </div>
    </>
  );
}
