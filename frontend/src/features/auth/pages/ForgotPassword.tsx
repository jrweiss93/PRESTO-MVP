import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import AuthShell from "@/features/auth/components/AuthShell";
import { ApiError } from "@/shared/api/client";
import * as api from "@/shared/api/endpoints";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.requestPasswordReset({ email });
      setSent(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo enviar el pedido. Verificá la conexión con la API.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Recuperar contraseña"
      subtitle="Ingresá tu email y te enviamos un enlace para elegir una nueva."
      sideTitle="Olvidaste tu contraseña, no tus finanzas."
      sideText="Por seguridad, el enlace vence en una hora y solo sirve una vez."
    >
      {sent ? (
        <>
          <div className="alert success">
            Si el email está registrado, te enviamos un enlace para restablecer
            la contraseña. Revisá también la carpeta de spam.
          </div>
          <p className="mt-6 text-center text-theme-sm text-gray-700">
            <Link to="/login" className="text-brand-500 hover:text-brand-600">
              Volver a iniciar sesión
            </Link>
          </p>
        </>
      ) : (
        <>
          {error && <div className="alert error">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-6">
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
            <button className="btn block" type="submit" disabled={submitting}>
              {submitting ? "Enviando…" : "Enviar enlace"}
            </button>
          </form>
          <p className="mt-6 text-center text-theme-sm text-gray-700">
            <Link to="/login" className="text-brand-500 hover:text-brand-600">
              Volver a iniciar sesión
            </Link>
          </p>
        </>
      )}
    </AuthShell>
  );
}
