"use client";

/**
 * AuthContext — provides the current token + login / logout helpers to the
 * entire React tree.  The token itself lives in localStorage (via lib/auth.ts).
 * Components that read `useAuth()` re-render whenever the user logs in or out.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { clearToken, getToken, setToken } from "../../lib/auth";

/* ── types ────────────────────────────────────────────────────────────────── */

interface AuthContextValue {
  token: string | null;
  /** Call after a successful /auth/login or /auth/signup response */
  login: (token: string) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

/* ── context ──────────────────────────────────────────────────────────────── */

const AuthContext = createContext<AuthContextValue | null>(null);

/* ── provider ─────────────────────────────────────────────────────────────── */

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);

  // Hydrate from localStorage once the component mounts (client only)
  useEffect(() => {
    setTokenState(getToken());
  }, []);

  const login = useCallback((newToken: string) => {
    setToken(newToken);
    setTokenState(newToken);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, login, logout, isLoggedIn: Boolean(token) }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/* ── hook ─────────────────────────────────────────────────────────────────── */

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
