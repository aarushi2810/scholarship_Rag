"use client";
/**
 * Thin client-side wrapper that applies AuthGuard to the dashboard.
 * The actual page content is rendered by the server component (page.tsx)
 * which Next.js automatically passes as children via the layout system.
 * We use a separate layout so we don't lose the async server component benefits.
 */
import { AuthGuard } from "../components/AuthGuard";
import { type ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
