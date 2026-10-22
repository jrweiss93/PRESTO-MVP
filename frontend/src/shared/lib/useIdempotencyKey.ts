import { useCallback, useRef } from "react";
import { newIdempotencyKey } from "@/shared/api/client";

/**
 * Clave de idempotencia estable por intento del usuario: se genera la
 * primera vez que se manda la operación y se reutiliza en los reintentos de
 * ese mismo intento. Tras un éxito se resetea para que la próxima operación
 * tenga su propia clave (PROYECTO_FRONT.md §6.1).
 */
export function useIdempotencyKey() {
  const keyRef = useRef<string | null>(null);

  const get = useCallback(() => {
    if (!keyRef.current) keyRef.current = newIdempotencyKey();
    return keyRef.current;
  }, []);

  const reset = useCallback(() => {
    keyRef.current = null;
  }, []);

  return { get, reset };
}
