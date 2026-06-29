"use client";

/**
 * AuthGuard — wraps any page that requires a logged-in user.
 * If no token is found in localStorage, it redirects to /login immediately.
 * While hydrating (first render on the client) it shows nothing to avoid flash.
 */

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { useAuth } from "./AuthContext";

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

  if (!ready) return null;
  return <>{children}</>;
}
