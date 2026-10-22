// El asistente "Presti" ya está implementado en el backend (`apps/assistant`):
// mercado, noticias, marco legal y chat por reglas, sin LLM. Se puede apagar
// con VITE_ENABLE_ASSISTANT=false si se quiere una UI más chica.
export const ENABLE_ASSISTANT =
  import.meta.env.VITE_ENABLE_ASSISTANT !== "false";
