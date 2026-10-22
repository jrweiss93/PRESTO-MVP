import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import { ApiError } from "@/shared/api/client";
import { EyeCloseIcon, EyeIcon } from "@/shared/ui/icons";

export default function Register() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (password.length < 10) {
      setError("La contraseña debe tener al menos 10 caracteres.");
      return;
    }
    setSubmitting(true);
    try {
      await register(email, password);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo registrar. Verificá la conexión con la API.",
      );
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <div className="flex w-full flex-col justify-between bg-brand-500 px-6 py-10 sm:px-10 lg:w-2/5 lg:py-12 xl:w-1/3">
        <Link to="/" className="text-title-sm font-semibold text-white">
          Presto<span className="text-brand-100">.</span>
        </Link>
        <div className="my-10">
          <h2 className="mb-4 text-title-sm font-semibold text-white">
            Unite a Presto y hacé crecer tu dinero.
          </h2>
          <p className="max-w-md text-theme-sm text-brand-100">
            Creá tu cuenta, completá la verificación KYC y empezá a invertir o a
            solicitar préstamos en minutos.
          </p>
        </div>
        <p className="text-theme-xs text-brand-100">
          © {new Date().getFullYear()} Presto. Todos los derechos reservados.
        </p>
      </div>

      <div className="flex flex-1 flex-col justify-center bg-white px-6 py-10 sm:px-12 lg:px-16">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8">
            <h1 className="mb-2 text-title-sm font-semibold text-gray-800">
              Crear cuenta
            </h1>
            <p className="text-theme-sm text-gray-500">
              Completá tus datos para registrarte en Presto.
            </p>
          </div>

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
                placeholder="••••••••"
                className="h-11"
              />
            </div>
            <button className="btn block" type="submit" disabled={submitting}>
              {submitting ? "Creando cuenta…" : "Registrarme"}
            </button>
          </form>

          <div className="mt-6">
            <p className="text-center text-theme-sm text-gray-700">
              ¿Ya tenés cuenta?{" "}
              <Link to="/login" className="text-brand-500 hover:text-brand-600">
                Iniciá sesión
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
