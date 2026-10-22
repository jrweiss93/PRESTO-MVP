import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import { ApiError } from "@/shared/api/client";
import { EyeCloseIcon, EyeIcon } from "@/shared/ui/icons";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo iniciar sesión. Verificá la conexión con la API.",
      );
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <div className="flex w-full flex-col justify-between bg-brand-500 px-6 py-10 sm:px-10 lg:w-2/5 lg:py-12 xl:w-1/3">
        <Link to="/login" className="text-title-sm font-semibold text-white">
          Presto<span className="text-brand-100">.</span>
        </Link>
        <div className="my-10">
          <h2 className="mb-4 text-title-sm font-semibold text-white">
            Invertí y pedí prestado de forma simple, segura y transparente.
          </h2>
          <p className="max-w-md text-theme-sm text-brand-100">
            Plataforma P2P de préstamos e inversiones en pesos y dólares.
            Completá tu KYC, publicá o financiá ofertas y seguí todo en tiempo
            real.
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
              Iniciar sesión
            </h1>
            <p className="text-theme-sm text-gray-500">
              Ingresá tu email y contraseña para continuar.
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
                  autoComplete="current-password"
                  placeholder="••••••••"
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
            <button className="btn block" type="submit" disabled={submitting}>
              {submitting ? "Ingresando…" : "Ingresar"}
            </button>
          </form>

          <div className="mt-4 text-end">
            <Link
              to="/recuperar"
              className="text-theme-sm text-brand-500 hover:text-brand-600"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>

          <div className="mt-6">
            <p className="text-center text-theme-sm text-gray-700">
              ¿No tenés cuenta?{" "}
              <Link
                to="/registro"
                className="text-brand-500 hover:text-brand-600"
              >
                Registrate
              </Link>
            </p>
          </div>

          <div className="mt-8 rounded-lg bg-gray-50 p-4 text-theme-xs text-gray-500">
            <p className="mb-1 font-medium text-gray-700">
              Cuentas de demostración:
            </p>
            <p>Prestataria: ana@presto.demo / Presto123!</p>
            <p>Prestamista: beto@presto.demo / Presto123!</p>
            <p>Inversora: carla@presto.demo / Presto123!</p>
          </div>
        </div>
      </div>
    </div>
  );
}
