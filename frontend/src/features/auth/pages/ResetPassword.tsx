import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthShell from "@/features/auth/components/AuthShell";
import { ApiError } from "@/shared/api/client";
import * as api from "@/shared/api/endpoints";
import { EyeCloseIcon, EyeIcon } from "@/shared/ui/icons";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const missingLink = !uid || !token;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    setSubmitting(true);
    try {
      await api.confirmPasswordReset({
        uid,
        token,
        new_password: password,
      });
      setDone(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo cambiar la contraseña. Verificá la conexión con la API.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Nueva contraseña"
      subtitle="Elegí una contraseña nueva para tu cuenta."
      sideTitle="Un enlace, una contraseña nueva."
      sideText="Cuando la cambies, todas las sesiones abiertas se cierran por seguridad."
    >
      {missingLink ? (
        <>
          <div className="alert error">
            El enlace está incompleto o venció. Pedí uno nuevo.
          </div>
          <Link to="/recuperar" className="btn block">
            Pedir otro enlace
          </Link>
        </>
      ) : done ? (
        <>
          <div className="alert success">
            Contraseña actualizada. Ya podés iniciar sesión con la nueva.
          </div>
          <Link to="/login" className="btn block">
            Iniciar sesión
          </Link>
        </>
      ) : (
        <>
          {error && <div className="alert error">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="password"
                className="label.field mb-1.5 block text-theme-sm font-medium text-gray-700"
              >
                Contraseña nueva <span className="text-error-500">*</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                  placeholder="Mínimo 8 caracteres"
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
                htmlFor="confirm"
                className="label.field mb-1.5 block text-theme-sm font-medium text-gray-700"
              >
                Repetir contraseña <span className="text-error-500">*</span>
              </label>
              <input
                id="confirm"
                name="confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                autoComplete="new-password"
                placeholder="••••••••"
                className="h-11"
              />
            </div>
            <button className="btn block" type="submit" disabled={submitting}>
              {submitting ? "Guardando…" : "Cambiar contraseña"}
            </button>
          </form>
          <p className="mt-6 text-center text-theme-sm text-gray-700">
            ¿El enlace venció?{" "}
            <Link to="/recuperar" className="text-brand-500 hover:text-brand-600">
              Pedí otro
            </Link>
          </p>
        </>
      )}
    </AuthShell>
  );
}
