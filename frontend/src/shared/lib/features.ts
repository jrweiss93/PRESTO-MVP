// Features del front que dependen de endpoints que el backend todavía no
// expone. El asistente "Presti" solo existe en el mock (docs/decisions.md D-5):
// contra la API real esas pantallas fallan, así que por defecto se ocultan.
// Para verlas contra el mock: VITE_ENABLE_ASSISTANT=true.
export const ENABLE_ASSISTANT =
  import.meta.env.VITE_ENABLE_ASSISTANT === "true";
