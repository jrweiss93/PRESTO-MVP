import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import type { Meta } from "@/shared/api/types";

const DISMISS_KEY = "presto.demo-banner.dismissed";

/**
 * Aviso visible en la demo: el dinero es simulado. Se apoya en `/api/v1/meta/`
 * para no mostrarse en una instancia con dinero real.
 */
export default function DemoModeBanner() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    try {
      setDismissed(sessionStorage.getItem(DISMISS_KEY) === "1");
    } catch {
      setDismissed(false);
    }
    let active = true;
    api
      .getMeta()
      .then((data) => {
        if (active) setMeta(data);
      })
      .catch(() => {
        if (active) setMeta(null);
      });
    return () => {
      active = false;
    };
  }, []);

  if (meta?.mode !== "demo" || dismissed) return null;

  function dismiss() {
    setDismissed(true);
    try {
      sessionStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // sin sessionStorage se descarta solo en esta sesión
    }
  }

  return (
    <div className="border-b border-blue-200 bg-blue-50 px-4 py-2 text-xs text-blue-900">
      <div className="mx-auto flex max-w-(--breakpoint-2xl) items-center gap-3">
        <p className="flex-1">
          <strong>Estás en la demo de Presto.</strong> El dinero es simulado y
          no se mueve plata real.{" "}
          <Link to="/legal" className="underline">
            Ver alcance
          </Link>
          .
        </p>
        <button
          className="rounded border border-blue-300 px-2 py-1 text-blue-800 hover:bg-blue-100"
          onClick={dismiss}
          type="button"
        >
          Cerrar
        </button>
      </div>
    </div>
  );
}
