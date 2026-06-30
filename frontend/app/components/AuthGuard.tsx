"use client";

/**
 * AuthGuard — wraps any page that requires a logged-in user.
 * If no token is found in localStorage, it redirects to /login immediately.
 * While hydrating (first render on the client) it shows a skeleton layout
 * instead of a blank screen — prevents layout shift and white flash.
 */

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { useAuth } from "./AuthContext";

/* ── Hydration skeleton — mirrors the dashboard stat + card layout ──────────── */
function HydrationSkeleton() {
  return (
    <main className="page" aria-busy="true" aria-label="Loading">
      <div className="panel hero-panel" style={{ marginBottom: "18px" }}>
        <div className="skeleton skeleton--line skeleton--short" style={{ marginBottom: 8 }} />
        <div className="skeleton skeleton--title" style={{ width: "40%" }} />
      </div>

      <section className="stats-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="stat-card">
            <div className="skeleton skeleton--line skeleton--short" style={{ marginBottom: 8 }} />
            <div className="skeleton skeleton--title" style={{ width: "50%" }} />
          </div>
        ))}
      </section>

      <div className="grid">
        <aside className="stack">
          <section className="panel">
            <div className="skeleton skeleton--title" style={{ marginBottom: 12 }} />
            <div className="skeleton skeleton--line" style={{ marginBottom: 8 }} />
            <div className="skeleton skeleton--line skeleton--short" />
          </section>
        </aside>
        <section className="stack">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card skeleton-card">
              <div className="skeleton skeleton--title" />
              <div className="skeleton skeleton--line" />
              <div className="skeleton skeleton--line skeleton--short" />
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}

export function AuthGuard({ children }: { children: ReactNode }) {
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // After hydration we know for certain whether a token exists
    if (!isLoggedIn) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [isLoggedIn, router]);

  // Show skeleton during hydration instead of a blank screen
  if (!ready) return <HydrationSkeleton />;
  return <>{children}</>;
}
