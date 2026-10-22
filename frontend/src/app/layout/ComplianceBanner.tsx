import { useEffect, useState } from "react";
import * as api from "@/shared/api/endpoints";
import type { Meta } from "@/shared/api/types";

const DISMISS_KEY = "presto.compliance.dismissed";

function bannerEnabled(mode: string): boolean {
  const hide = import.meta.env.VITE_HIDE_COMPLIANCE_BANNER;
  if (hide === "true") return false;
  const force = import.meta.env.VITE_SHOW_COMPLIANCE_BANNER;
  if (force === "true") return true;
  // En modo demo (pitch) el recordatorio interno no se muestra.
  return mode !== "demo";
}

/**
 * Recordatorio interno: el backend expone en `/api/v1/meta/` los puntos que
 * todavía necesitan validación legal o profesional. No es un mensaje para el
 * usuario final del pitch: por eso queda oculto en modo demo y se puede
 * apagar con `VITE_HIDE_COMPLIANCE_BANNER=true`.
 */
export default function ComplianceBanner() {
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

  const compliance = meta?.compliance;
  if (!compliance || !compliance.legal_review_pending) return null;
  if (compliance.acknowledged) return null;
  if (dismissed) return null;
  if (!bannerEnabled(meta?.mode ?? "")) return null;

  function dismiss() {
    setDismissed(true);
    try {
      sessionStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // sin sessionStorage el banner se descarta solo en esta sesión
    }
  }

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-900">
      <div className="mx-auto flex max-w-(--breakpoint-2xl) items-start gap-3">
        <div className="flex-1">
          <p className="font-semibold">
            Recordatorio interno: revisión legal pendiente
          </p>
          <ul className="mt-1 list-disc pl-4">
            {compliance.items.map((item) => (
              <li key={item.id}>
                {item.label} ({item.doc})
              </li>
            ))}
          </ul>
        </div>
        <button
          className="rounded border border-amber-300 px-2 py-1 text-amber-800 hover:bg-amber-100"
          onClick={dismiss}
          type="button"
        >
          Descartar
        </button>
      </div>
    </div>
  );
}
