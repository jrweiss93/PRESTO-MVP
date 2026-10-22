import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface AuthShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  sideTitle?: string;
  sideText?: string;
}

/** Layout de las pantallas públicas de autenticación (login, reseteo, verificación). */
export default function AuthShell({
  title,
  subtitle,
  children,
  sideTitle = "Recuperá el acceso a tu cuenta de forma simple y segura.",
  sideText = "Te enviamos un enlace por email para que vuelvas a entrar sin perder nada de tu información.",
}: AuthShellProps) {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <div className="flex w-full flex-col justify-between bg-brand-500 px-6 py-10 sm:px-10 lg:w-2/5 lg:py-12 xl:w-1/3">
        <Link to="/login" className="text-title-sm font-semibold text-white">
          Presto<span className="text-brand-100">.</span>
        </Link>
        <div className="my-10">
          <h2 className="mb-4 text-title-sm font-semibold text-white">
            {sideTitle}
          </h2>
          <p className="max-w-md text-theme-sm text-brand-100">{sideText}</p>
        </div>
        <p className="text-theme-xs text-brand-100">
          © {new Date().getFullYear()} Presto. Todos los derechos reservados.
        </p>
      </div>

      <div className="flex flex-1 flex-col justify-center bg-white px-6 py-10 sm:px-12 lg:px-16">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8">
            <h1 className="mb-2 text-title-sm font-semibold text-gray-800">
              {title}
            </h1>
            <p className="text-theme-sm text-gray-500">{subtitle}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
