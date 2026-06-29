"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { useAuth } from "../components/AuthContext";
import { signupUser } from "../../lib/api";

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const data = await signupUser({ email, password });
      login(data.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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

        <h1 className="auth-heading">Create your account</h1>
        <p className="auth-sub">Start finding scholarships that match you</p>

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="auth-field-group">
            <label htmlFor="reg-email" className="auth-label">
              Email address
            </label>
            <input
              id="reg-email"
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
            <label htmlFor="reg-password" className="auth-label">
              Password
              <span className="auth-hint">min. 8 characters</span>
            </label>
            <input
              id="reg-password"
              type="password"
              className="field"
              placeholder="••••••••"
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="auth-field-group">
            <label htmlFor="reg-confirm" className="auth-label">
              Confirm password
            </label>
            <input
              id="reg-confirm"
              type="password"
              className="field"
              placeholder="••••••••"
              autoComplete="new-password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
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
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link href="/login" className="auth-link">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
