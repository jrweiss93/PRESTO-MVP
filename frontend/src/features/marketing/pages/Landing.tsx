import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import {
  CartIcon,
  DollarLineIcon,
  PieChartIcon,
  SparkIcon,
} from "@/shared/ui/icons";

const FEATURES = [
  {
    title: "Billetera en ARS y USD",
    text: "Depositá, retirá y transferí sin mezclar monedas. El saldo lo lleva un libro mayor de doble entrada.",
    icon: <DollarLineIcon className="size-6 text-brand-500" />,
  },
  {
    title: "Marketplace de préstamos",
    text: "Publicá una oferta como prestamista o compará tasas, plazos y cuotas antes de aceptar.",
    icon: <CartIcon className="size-6 text-brand-500" />,
  },
  {
    title: "Plazos fijos",
    text: "Invertí tu saldo a plazo fijo y seguí el interés y el vencimiento desde el panel.",
    icon: <PieChartIcon className="size-6 text-brand-500" />,
  },
  {
    title: "Presti, el asistente",
    text: "Consultá tu saldo, tus cuotas, el mercado y el marco legal. Sin humo y sin inventar.",
    icon: <SparkIcon className="size-6 text-brand-500" />,
  },
];

const DEMO_USERS = [
  { role: "Prestataria", email: "ana@presto.demo" },
  { role: "Prestamista", email: "beto@presto.demo" },
  { role: "Inversora", email: "carla@presto.demo" },
];

export default function Landing() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link to="/" className="text-title-sm font-semibold text-gray-800">
            Presto<span className="text-brand-500">.</span>
          </Link>
          <nav className="flex items-center gap-3">
            <Link
              to="/legal"
              className="hidden text-theme-sm text-gray-600 hover:text-gray-900 sm:block"
            >
              Legal
            </Link>
            {user ? (
              <Link to="/dashboard" className="btn">
                Ir al panel
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-theme-sm text-gray-700 hover:text-gray-900"
                >
                  Ingresar
                </Link>
                <Link to="/registro" className="btn">
                  Crear cuenta
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <div className="border-b border-amber-200 bg-amber-50 px-5 py-2 text-center text-theme-xs text-amber-900">
        <strong>Demo pública.</strong> El dinero es simulado: no se mueve plata
        real.{" "}
        <Link to="/legal" className="underline">
          Ver alcance
        </Link>
      </div>

      <main>
        <section className="mx-auto grid max-w-6xl gap-10 px-5 py-14 lg:grid-cols-2 lg:items-center lg:py-20">
          <div>
            <span className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-theme-xs font-medium text-brand-600">
              Finanzas P2P · ARS y USD
            </span>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
              Prestá, pedí prestado e invertí de forma simple.
            </h1>
            <p className="mt-4 max-w-xl text-base text-gray-600">
              Presto conecta personas que quieren prestar con personas que
              necesitan financiarse. Todo en un solo lugar: billetera, ofertas,
              cuotas, inversiones y reportes.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to={user ? "/dashboard" : "/login"} className="btn">
                {user ? "Ir al panel" : "Entrar a la demo"}
              </Link>
              {!user && (
                <Link
                  to="/registro"
                  className="rounded-lg border border-gray-300 px-5 py-2.5 text-center text-theme-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Crear una cuenta
                </Link>
              )}
            </div>
            <p className="mt-4 text-theme-xs text-gray-500">
              No es una oferta pública de inversión ni asesoramiento financiero.
            </p>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-6">
            <h2 className="text-base font-semibold text-gray-800">
              Cuentas de demostración
            </h2>
            <p className="mt-1 text-theme-sm text-gray-600">
              Entrá con cualquiera de estos usuarios para ver el circuito
              completo.
            </p>
            <ul className="mt-4 space-y-2">
              {DEMO_USERS.map((demo) => (
                <li
                  key={demo.email}
                  className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3"
                >
                  <div>
                    <p className="text-theme-sm font-medium text-gray-800">
                      {demo.role}
                    </p>
                    <p className="font-mono text-theme-xs text-gray-500">
                      {demo.email}
                    </p>
                  </div>
                  <span className="text-theme-xs text-gray-500">
                    Presto123!
                  </span>
                </li>
              ))}
            </ul>
            <Link
              to="/login"
              className="mt-5 block rounded-lg bg-brand-500 px-4 py-2.5 text-center text-theme-sm font-medium text-white hover:bg-brand-600"
            >
              Iniciar sesión
            </Link>
            <p className="mt-3 text-theme-xs text-gray-500">
              Los datos y los saldos son de ejemplo. No uses datos personales
              reales en esta demo.
            </p>
          </div>
        </section>

        <section className="border-t border-gray-200 bg-gray-50/60">
          <div className="mx-auto max-w-6xl px-5 py-14">
            <h2 className="text-2xl font-semibold text-gray-900">
              Todo el circuito, en un solo lugar
            </h2>
            <p className="mt-2 max-w-2xl text-theme-sm text-gray-600">
              Desde el alta y el KYC hasta el pago de la última cuota. Sin
              planillas y sin cálculos a mano.
            </p>
            <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map((feature) => (
                <article
                  key={feature.title}
                  className="rounded-xl border border-gray-200 bg-white p-5"
                >
                  <div className="mb-3">{feature.icon}</div>
                  <h3 className="text-theme-sm font-semibold text-gray-800">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-theme-sm text-gray-600">
                    {feature.text}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 py-14">
          <div className="grid gap-8 lg:grid-cols-3">
            <div>
              <span className="text-theme-xs font-semibold tracking-wide text-brand-500 uppercase">
                Cómo probar
              </span>
              <h2 className="mt-2 text-2xl font-semibold text-gray-900">
                Tres pasos y ya estás operando
              </h2>
            </div>
            <ol className="space-y-4 lg:col-span-2">
              <li className="flex gap-3">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-500 text-theme-xs font-semibold text-white">
                  1
                </span>
                <p className="text-theme-sm text-gray-700">
                  Entrá con una cuenta de demo o creá la tuya. El KYC se aprueba
                  desde el panel de administración.
                </p>
              </li>
              <li className="flex gap-3">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-500 text-theme-xs font-semibold text-white">
                  2
                </span>
                <p className="text-theme-sm text-gray-700">
                  Depositá saldo simulado, publicá una oferta o aceptá una del
                  marketplace y pagá una cuota.
                </p>
              </li>
              <li className="flex gap-3">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-500 text-theme-xs font-semibold text-white">
                  3
                </span>
                <p className="text-theme-sm text-gray-700">
                  Abrí un plazo fijo, armá un presupuesto y preguntale a Presti
                  por tu saldo o el marco legal.
                </p>
              </li>
            </ol>
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-8 text-theme-xs text-gray-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Presto. Demo con dinero simulado.</p>
          <div className="flex gap-4">
            <Link to="/legal" className="hover:text-gray-700">
              Legal y alcance
            </Link>
            <Link to="/login" className="hover:text-gray-700">
              Ingresar
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
