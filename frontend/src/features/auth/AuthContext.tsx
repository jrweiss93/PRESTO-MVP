import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getAccessToken, setAccessToken } from "@/shared/api/client";
import * as api from "@/shared/api/endpoints";
import type { LoginResponse, User } from "@/shared/api/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Al abrir la app se intenta recuperar la sesión con el refresh cookie
  // (httpOnly, invisible para el front). Si no hay sesión, el usuario queda
  // deslogueado y la app muestra el login.
  const loadUser = useCallback(async () => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1"}/auth/token/refresh/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        },
      );
      if (res.ok) {
        const data = (await res.json()) as { access?: string };
        if (data.access) setAccessToken(data.access);
      }
    } catch {
      // sin cookie de refresh: se sigue como deslogueado
    }
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api.me());
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUser();
  }, [loadUser]);

  const login = useCallback(async (email: string, password: string) => {
    const res: LoginResponse = await api.login({ email, password });
    // Solo el access token queda en memoria. El refresh viaja en la cookie
    // httpOnly que deja el backend (ADR 0014).
    setAccessToken(res.access);
    setUser(res.user);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await api.register({ email, password });
    const res = await api.login({ email, password });
    setAccessToken(res.access);
    setUser(res.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // el logout local se hace igual
    }
    setAccessToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(await api.me());
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
