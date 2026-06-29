/**
 * Token helpers — thin wrappers around localStorage so the rest of the
 * codebase never hard-codes the key name or touches localStorage directly.
 *
 * All functions are safe to call during SSR (they return null / no-op when
 * `window` is not defined).
 */

const KEY = "sm_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}

export function isLoggedIn(): boolean {
  return Boolean(getToken());
}
