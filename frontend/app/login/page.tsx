"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { useAuth } from "../components/AuthContext";
import { loginUser } from "../../lib/api";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await loginUser({ email, password });
      login(data.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card fade-in">
        {/* Logo */}
        <div className="auth-brand">
          <div className="brand-mark">SM</div>
          <span className="auth-brand-name">ScholarMatch AI</span>
        </div>

        <h1 className="auth-heading">Welcome back</h1>
        <p className="auth-sub">Sign in to your account to continue</p>

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="auth-field-group">
            <label htmlFor="login-email" className="auth-label">
              Email address
            </label>
            <input
              id="login-email"
              type="email"
              className="field"
              placeholder="you@example.com"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="auth-field-group">
            <label htmlFor="login-password" className="auth-label">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              className="field"
              placeholder="••••••••"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="button primary auth-submit"
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="auth-link">
            Create one
          </Link>
        </p>
      </div>
    </main>
  );
}
