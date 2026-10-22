import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthShell from "@/features/auth/components/AuthShell";
import { useAuth } from "@/features/auth/AuthContext";
import * as api from "@/shared/api/endpoints";

type State = "loading" | "ok" | "error";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";
  const { user, refreshUser } = useAuth();
  const [state, setState] = useState<State>("loading");
  const [message, setMessage] = useState("");
  const requested = useRef(false);

  useEffect(() => {
    if (requested.current) return;
    requested.current = true;
    if (!uid || !token) {
      setState("error");
      setMessage(
        "El enlace está incompleto o venció. Pedí uno nuevo desde tu perfil.",
      );
      return;
    }
    api
      .verifyEmail({ uid, token })
      .then(() => {
        setState("ok");
        if (user) void refreshUser().catch(() => undefined);
      })
      .catch((err: unknown) => {
        setState("error");
        setMessage(
          err instanceof Error
            ? err.message
            : "No se pudo verificar el email. Probá de nuevo.",
        );
      });
  }, [uid, token, user, refreshUser]);

  return (
    <AuthShell
      title="Confirmar email"
      subtitle="Estamos verificando tu dirección."
      sideTitle="Tu email, confirmado."
      sideText="Con la dirección verificada podemos avisarte de tus cuotas, inversiones y movimientos."
    >
      {state === "loading" && (
        <div className="alert">Verificando tu email…</div>
      )}
      {state === "ok" && (
        <>
          <div className="alert success">
            ¡Listo! Tu email quedó verificado.
          </div>
          <Link to={user ? "/dashboard" : "/login"} className="btn block">
            {user ? "Ir al panel" : "Iniciar sesión"}
          </Link>
        </>
      )}
      {state === "error" && (
        <>
          <div className="alert error">{message}</div>
          <Link to="/login" className="btn block">
            Volver al inicio
          </Link>
        </>
      )}
    </AuthShell>
  );
}
