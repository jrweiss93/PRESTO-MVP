import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth, type RegisterIdentity } from "@/features/auth/AuthContext";
import { ApiError } from "@/shared/api/client";
import ThemeToggle from "@/shared/ui/ThemeToggle";
import type { ProfileKind } from "@/shared/api/types";
import { PROFILE_KINDS, PROFILE_LABELS } from "@/shared/lib/profiles";
import {
  CheckCircleIcon,
  EyeCloseIcon,
  EyeIcon,
  FileIcon,
  UserCircleIcon,
} from "@/shared/ui/icons";

type CredentialType = RegisterIdentity["credential_type"];

export default function Register() {
  const { register } = useAuth();
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [profileKind, setProfileKind] = useState<ProfileKind>("borrower");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [dni, setDni] = useState("");
  const [dniScanned, setDniScanned] = useState(false);
  const [scanningDni, setScanningDni] = useState(false);
  const [credentialType, setCredentialType] =
    useState<CredentialType>("license");
  const [credentialVerified, setCredentialVerified] = useState(false);
  const [scanningCredential, setScanningCredential] = useState(false);
  const [faceVerified, setFaceVerified] = useState(false);
  const [scanningFace, setScanningFace] = useState(false);

  const identityComplete =
    dniScanned && credentialVerified && faceVerified;

  function validateAccount() {
    if (!acceptedTerms) {
      setError("Debés aceptar los términos y condiciones para continuar.");
      return false;
    }
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return false;
    }
    if (password.length < 10) {
      setError("La contraseña debe tener al menos 10 caracteres.");
      return false;
    }
    return true;
  }

  function handleContinue(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (validateAccount()) setStep(2);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!validateAccount()) return;
    if (!identityComplete) {
      setError("Completá las tres validaciones simuladas para crear la cuenta.");
      return;
    }
    setSubmitting(true);
    try {
      await register(email, password, profileKind, {
        dni,
        credential_type: credentialType,
        credential_verified: true,
        face_verified: true,
      });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo registrar. Verificá la conexión con la API.",
      );
      setSubmitting(false);
    }
  }

  function simulateDni() {
    if (!/^\d{7,8}$/.test(dni)) {
      setError("Ingresá un DNI de 7 u 8 dígitos para simular el escaneo.");
      return;
    }
    setError(null);
    setScanningDni(true);
    window.setTimeout(() => {
      setScanningDni(false);
      setDniScanned(true);
    }, 900);
  }

  function simulateCredential() {
    setError(null);
    setScanningCredential(true);
    window.setTimeout(() => {
      setScanningCredential(false);
      setCredentialVerified(true);
    }, 900);
  }

  function simulateFace() {
    setError(null);
    setScanningFace(true);
    window.setTimeout(() => {
      setScanningFace(false);
      setFaceVerified(true);
    }, 1800);
  }

  return (
    <div className="auth-page flex min-h-screen flex-col lg:flex-row">
      <div className="auth-hero flex w-full flex-col justify-between px-6 py-10 sm:px-10 lg:w-2/5 lg:py-12 xl:w-1/3">
        <Link to="/" className="text-title-sm font-semibold text-white">
          Presto<span className="text-brand-100">.</span>
        </Link>
        <div className="my-10">
          <h2 className="mb-4 text-title-sm font-semibold text-white">
            Unite a Presto y hacé crecer tu dinero.
          </h2>
          <p className="max-w-md text-theme-sm text-brand-100">
            Creá tu cuenta, completá la verificación simulada de identidad y
            empezá a invertir o a solicitar préstamos en minutos.
          </p>
          <div className="mt-6 space-y-2 text-theme-xs text-brand-100">
            <p>✓ DNI y credencial simulados</p>
            <p>✓ Prueba de vida y coincidencia facial</p>
            <p>✓ Sin selfies ni documentos reales</p>
          </div>
        </div>
        <p className="text-theme-xs text-brand-100">
          © {new Date().getFullYear()} Presto. Todos los derechos reservados.
        </p>
      </div>

      <div className="flex flex-1 flex-col justify-center bg-white px-6 py-10 sm:px-12 lg:px-16 dark:bg-gray-950">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <span className={`step-dot${step >= 1 ? " active" : ""}`}>1</span>
                <span className="step-line" />
                <span className={`step-dot${step >= 2 ? " active" : ""}`}>2</span>
                <span className="ml-1 text-theme-xs font-medium text-gray-500">
                  {step === 1 ? "Datos de cuenta" : "Verificación simulada"}
                </span>
              </div>
              <h1 className="mb-2 text-title-sm font-semibold text-gray-800">
                {step === 1 ? "Crear cuenta" : "Verificá tu identidad"}
              </h1>
              <p className="text-theme-sm text-gray-500">
                {step === 1
                  ? "Completá tus datos para registrarte en Presto."
                  : "Simulación de demo: no se envía una selfie ni se guarda el DNI completo."}
              </p>
            </div>
            <ThemeToggle />
          </div>

          {error && <div className="alert error">{error}</div>}

          <form
            onSubmit={step === 1 ? handleContinue : handleSubmit}
            className="space-y-5"
          >
            {step === 1 ? (
              <>
                <div>
                  <label
                    htmlFor="profile-kind"
                    className="label.field mb-1.5 block text-theme-sm font-medium text-gray-700"
                  >
                    Perfil <span className="text-error-500">*</span>
                  </label>
                  <select
                    id="profile-kind"
                    name="profile-kind"
                    value={profileKind}
                    onChange={(e) =>
                      setProfileKind(e.target.value as ProfileKind)
                    }
                    required
                    className="h-11"
                  >
                    {PROFILE_KINDS.map((kind) => (
                      <option key={kind} value={kind}>
                        {PROFILE_LABELS[kind]}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1.5 text-theme-xs text-gray-500">
                    {profileKind === "borrower" &&
                      "Prestatario: pedís préstamos y pagás en cuotas."}
                    {profileKind === "lender" &&
                      "Prestamista: publicás ofertas y prestás tu dinero."}
                    {profileKind === "investor" &&
                      "Inversor: abrís plazos fijos y hacés rendir tu saldo."}
                  </p>
                </div>
                <div>
                  <label
                    htmlFor="email"
                    className="label.field mb-1.5 block text-theme-sm font-medium text-gray-700"
                  >
                    Email <span className="text-error-500">*</span>
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    placeholder="tu@email.com"
                    className="h-11"
                  />
                </div>
                <div>
                  <label
                    htmlFor="password"
                    className="label.field mb-1.5 block text-theme-sm font-medium text-gray-700"
                  >
                    Contraseña <span className="text-error-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={10}
                      autoComplete="new-password"
                      placeholder="Mínimo 10 caracteres"
                      className="h-11 pe-11"
                    />
                    <span
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-e-4 top-1/2 z-30 -translate-y-1/2 cursor-pointer text-gray-500"
                    >
                      {showPassword ? <EyeIcon /> : <EyeCloseIcon />}
                    </span>
                  </div>
                </div>
                <div>
                  <label
                    htmlFor="confirm-password"
                    className="label.field mb-1.5 block text-theme-sm font-medium text-gray-700"
                  >
                    Repetir contraseña <span className="text-error-500">*</span>
                  </label>
                  <input
                    id="confirm-password"
                    name="confirm-password"
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    autoComplete="new-password"
                    placeholder="Repetí tu contraseña"
                    className="h-11"
                  />
                </div>
                <label className="flex items-start gap-2 text-theme-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={acceptedTerms}
                    onChange={(e) => setAcceptedTerms(e.target.checked)}
                    className="mt-0.5 size-4 shrink-0 accent-brand-500 p-0"
                  />
                  <span>
                    Acepto los{" "}
                    <Link
                      to="/legal"
                      target="_blank"
                      className="text-brand-500 hover:text-brand-600"
                    >
                      Términos y Condiciones
                    </Link>{" "}
                    y la Política de Privacidad de Presto.
                  </span>
                </label>
                <button
                  className="btn w-full"
                  type="submit"
                  disabled={!acceptedTerms}
                >
                  Continuar a la verificación
                </button>
              </>
            ) : (
              <>
                <div className="alert">
                  Esta es una simulación de demo. No se procesan datos
                  biométricos ni se guarda el DNI completo: solo los últimos 4
                  dígitos y el resultado de la validación.
                </div>

                <div
                  className={`identity-card${dniScanned ? " done" : ""}`}
                >
                  <div className="identity-card-head">
                    <span className="identity-icon">
                      <UserCircleIcon className="size-5" />
                    </span>
                    <div>
                      <strong>DNI</strong>
                      <p className="small text-muted mb-0">
                        Escaneo simulado del documento
                      </p>
                    </div>
                    {dniScanned && (
                      <CheckCircleIcon className="identity-check size-5" />
                    )}
                  </div>
                  <div className="identity-action-row">
                    <input
                      value={dni}
                      onChange={(event) => {
                        setDni(event.target.value.replace(/\D/g, ""));
                        setDniScanned(false);
                      }}
                      inputMode="numeric"
                      maxLength={8}
                      placeholder="Ej. 30123456"
                      aria-label="DNI simulado"
                      className="h-10"
                    />
                    <button
                      className="btn secondary small"
                      type="button"
                      onClick={simulateDni}
                      disabled={scanningDni || dniScanned}
                    >
                      {scanningDni
                        ? "Escaneando…"
                        : dniScanned
                          ? "DNI listo"
                          : "Escanear DNI"}
                    </button>
                  </div>
                  {dniScanned && (
                    <p className="identity-success">
                      DNI detectado · ••••{dni.slice(-4)}
                    </p>
                  )}
                </div>

                <div
                  className={`identity-card${credentialVerified ? " done" : ""}`}
                >
                  <div className="identity-card-head">
                    <span className="identity-icon">
                      <FileIcon className="size-5" />
                    </span>
                    <div>
                      <strong>Credencial</strong>
                      <p className="small text-muted mb-0">
                        Documento secundario simulado
                      </p>
                    </div>
                    {credentialVerified && (
                      <CheckCircleIcon className="identity-check size-5" />
                    )}
                  </div>
                  <div className="identity-action-row">
                    <select
                      value={credentialType}
                      onChange={(event) => {
                        setCredentialType(event.target.value as CredentialType);
                        setCredentialVerified(false);
                      }}
                      aria-label="Tipo de credencial"
                      className="h-10"
                    >
                      <option value="dni">DNI</option>
                      <option value="license">Licencia de conducir</option>
                      <option value="passport">Pasaporte</option>
                    </select>
                    <button
                      className="btn secondary small"
                      type="button"
                      onClick={simulateCredential}
                      disabled={scanningCredential || credentialVerified}
                    >
                      {scanningCredential
                        ? "Validando…"
                        : credentialVerified
                          ? "Credencial lista"
                          : "Validar credencial"}
                    </button>
                  </div>
                  {credentialVerified && (
                    <p className="identity-success">
                      Credencial verificada · coincidencia 99%
                    </p>
                  )}
                </div>

                <div className={`identity-card${faceVerified ? " done" : ""}`}>
                  <div className="identity-card-head">
                    <span className="identity-icon">
                      <UserCircleIcon className="size-5" />
                    </span>
                    <div>
                      <strong>Rostro</strong>
                      <p className="small text-muted mb-0">
                        Prueba de vida y coincidencia facial simuladas
                      </p>
                    </div>
                    {faceVerified && (
                      <CheckCircleIcon className="identity-check size-5" />
                    )}
                  </div>
                  <div
                    className={`face-frame${scanningFace ? " scanning" : ""}${faceVerified ? " verified" : ""}`}
                  >
                    <UserCircleIcon className="size-12 text-brand-400" />
                    <span>
                      {faceVerified
                        ? "Rostro verificado"
                        : scanningFace
                          ? "Analizando gesto y rostro…"
                          : "Listo para la prueba de vida"}
                    </span>
                  </div>
                  <div className="identity-action-row">
                    <button
                      className="btn secondary small"
                      type="button"
                      onClick={simulateFace}
                      disabled={scanningFace || faceVerified}
                    >
                      {scanningFace
                        ? "Analizando…"
                        : faceVerified
                          ? "Rostro listo"
                          : "Iniciar validación facial"}
                    </button>
                    {faceVerified && (
                      <span className="identity-success">
                        Liveness 98% · Match 96%
                      </span>
                    )}
                  </div>
                </div>

                <div className="btn-row">
                  <button
                    className="btn secondary"
                    type="button"
                    onClick={() => {
                      setStep(1);
                      setError(null);
                    }}
                    disabled={submitting}
                  >
                    Volver
                  </button>
                  <button
                    className="btn"
                    type="submit"
                    disabled={submitting || !identityComplete}
                  >
                    {submitting ? "Creando cuenta…" : "Crear cuenta"}
                  </button>
                </div>
              </>
            )}
          </form>

          {step === 1 && (
            <div className="mt-6">
              <p className="text-center text-theme-sm text-gray-700">
                ¿Ya tenés cuenta?{" "}
                <Link to="/login" className="text-brand-500 hover:text-brand-600">
                  Iniciá sesión
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
