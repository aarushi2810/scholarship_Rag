"use client";

/**
 * AuthContext — provides the current token + login / logout helpers to the
 * entire React tree.  The token itself lives in localStorage (via lib/auth.ts).
 * Components that read `useAuth()` re-render whenever the user logs in or out.
 *
 * Performance: the decoded JWT payload (user id, email) is cached in context
 * so components never need to make a separate /profile fetch just to display
 * the user's name or email.
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
import { clearSearchCache } from "../../lib/api";

/* ── types ────────────────────────────────────────────────────────────────── */

/**
 * Lightweight profile extracted from the JWT payload — available immediately
 * after login without any additional network request.
 */
export interface CachedUser {
  id: number;
  email: string;
}

interface AuthContextValue {
  token: string | null;
  /** Decoded JWT data — available instantly after login, no /profile fetch needed */
  cachedUser: CachedUser | null;
  /** Call after a successful /auth/login or /auth/signup response */
  login: (token: string) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

/* ── JWT payload decoder (no library needed — just base64 decode) ──────────── */

function decodeJwtPayload(token: string): CachedUser | null {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join(""),
    );
    const payload = JSON.parse(jsonPayload) as { sub?: string; email?: string };
    if (!payload.sub || !payload.email) return null;
    return { id: Number(payload.sub), email: payload.email };
  } catch {
    return null;
  }
}

/* ── context ──────────────────────────────────────────────────────────────── */

const AuthContext = createContext<AuthContextValue | null>(null);

/* ── provider ─────────────────────────────────────────────────────────────── */

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [cachedUser, setCachedUser] = useState<CachedUser | null>(null);

  // Hydrate from localStorage once the component mounts (client only)
  useEffect(() => {
    const stored = getToken();
    if (stored) {
      setTokenState(stored);
      setCachedUser(decodeJwtPayload(stored));
    }
  }, []);

  const login = useCallback((newToken: string) => {
    setToken(newToken);
    setTokenState(newToken);
    setCachedUser(decodeJwtPayload(newToken));
  }, []);

  const logout = useCallback(() => {
    clearToken();
    clearSearchCache(); // drop client-side search cache on logout
    setTokenState(null);
    setCachedUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, cachedUser, login, logout, isLoggedIn: Boolean(token) }}
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
